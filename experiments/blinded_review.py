"""E10 dummy-only packet/import/report. No genuine reviewers, cases or execution."""

import asyncio
import hashlib
import random
from statistics import mean
from typing import Literal

from psycopg.types.json import Jsonb
from pydantic import StrictInt

from experiments import synthetic_collection as replay
from future_training.agent.protocol import canonical
from future_training.approval import finish_owned
from future_training.domain.catalog import load_catalog
from future_training.experiments.model_evaluation import load_suite, run_case
from future_training.experiments.model_review import (
    DIMENSIONS,
    REVIEW_SEED,
    RUBRIC_VERSION,
    validate_ratings,
)

ROOT = replay.ROOT
SPEC = "docs/implementation/f3-e10-review-contract.md"
REVIEWERS = ("dummy-01", "dummy-02")
LIMIT = 262144


def digest(value):
    return replay.cases.sealed.digest(value)


def freeze():
    base = replay.freeze()
    files = dict(base["files"])
    for name in (SPEC, "tests/test_blinded_review.py"):
        files[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    body = dict(
        version="evaluation-configuration-freeze-v5",
        status="candidate_not_owner_approved",
        files=dict(sorted(files.items())),
        execution_configuration=base["fingerprint"],
        selection=base["selection_sha256"],
        rubric=RUBRIC_VERSION,
        historical_e9_sha256=hashlib.sha256(
            (ROOT / "docs/implementation/evidence/f3-e9-freeze-candidate.json").read_bytes()
        ).hexdigest(),
        live_enabled=False,
        monetary_authority=False,
    )
    return {**body, "fingerprint": digest(body)}


class Submission(replay.cases.Private):
    version: Literal["dummy-blinded-review-v1"]
    evidence: Literal["synthetic_dummy_not_human"]
    rubric: Literal["synthetic-plan-human-rubric-v1"]
    packet_id: replay.cases.Digest
    pair_id: str
    label: Literal["A", "B"]
    reviewer: Literal["dummy-01", "dummy-02"]
    judgment_status: Literal["rated_dummy", "abstained_dummy"]
    ratings: dict[str, StrictInt | None]
    explanation_clarity: None
    abstention_reason: (
        Literal["unjudgeable", "insufficient_information", "conflict_of_interest"] | None
    )


def parse(raw):
    try:
        v = replay.cases.json_object(raw, 16384)
        s = Submission.model_validate_json(canonical(v))
        if len(s.pair_id) > 64 or set(s.ratings) != set(DIMENSIONS):
            raise ValueError
        if s.judgment_status == "abstained_dummy":
            if s.abstention_reason is None or any(v is not None for v in s.ratings.values()):
                raise ValueError
        elif s.abstention_reason is not None:
            raise ValueError
        return s.model_dump(mode="json")
    except Exception:
        raise ValueError("dummy_submission_invalid") from None


def display(plan):
    # Both variants get the same view. No source/model/scoring/billing metadata.
    catalog = load_catalog()
    return dict(
        days=[
            {
                **day,
                "blocks": [
                    {
                        "exercise": catalog.get(block["exercise_id"]).title,
                        **{k: v for k, v in block.items() if k != "exercise_id"},
                    }
                    for block in day["blocks"]
                ],
            }
            for day in plan["days"]
        ]
    )


DDL = """CREATE TABLE IF NOT EXISTS experiment_e10_packet (
 slot integer PRIMARY KEY CHECK(slot=1), bundle jsonb NOT NULL,
 CHECK(octet_length(bundle::text)<262144));
 CREATE TABLE IF NOT EXISTS experiment_e10_reviews (
 ordinal integer CHECK(ordinal BETWEEN 1 AND 10), label text CHECK(label IN ('A','B')),
 reviewer text CHECK(reviewer IN ('dummy-01','dummy-02')),
 binding text NOT NULL, submission_sha text NOT NULL CHECK(length(submission_sha)=64),
 result jsonb CHECK(result IS NULL OR octet_length(result::text)<16384),
 PRIMARY KEY(ordinal,label,reviewer));
 CREATE TABLE IF NOT EXISTS experiment_e10_events (
 id bigint GENERATED ALWAYS AS IDENTITY (MAXVALUE 128 NO CYCLE) PRIMARY KEY,
 kind text NOT NULL CHECK(kind IN ('invalid','conflict','duplicate')))"""


class Review:
    def __init__(self, collection):
        if type(collection) is not replay.Collection:
            raise ValueError("exact_public_replay_collection_required")
        self.auto = collection
        self.configuration = freeze()
        if self.configuration["execution_configuration"] != collection.header["configuration"]:
            raise ValueError("review_source_mismatch")

    def check_source(self):
        self.auto.check_source()
        if canonical(freeze()) != canonical(self.configuration):
            raise ValueError("review_source_mismatch")

    async def initialize(self):
        self.check_source()
        async with asyncio.timeout(5):
            c = await self.auto.connection()
            try:
                await self.auto.check_header(c)
                await c.execute(DDL)
                await c.commit()
            except Exception:
                raise ValueError("review_initialization_uncertain") from None
            finally:
                await c.close()

    def path(self, name):
        # Caller never selects storage. Different CWD/packet/reviewer IDs cannot reset slots.
        directory = ROOT / ".cache/f3-e10/fences" / self.auto.schema
        if any(p.is_symlink() or p.is_junction() for p in (directory, *directory.parents)):
            raise ValueError("review_path_rejected")
        directory.mkdir(parents=True, exist_ok=True)
        return directory / name

    async def snapshot(self):
        rows = await self.auto.rows()
        state = []
        for i in range(1, 11):
            row = next((r for r in rows if r[0] == i), None)
            state.append(dict(ordinal=i, row=row, fence=self.auto.fence_path(i).exists()))
        return state

    async def build(self):
        self.check_source()
        snapshot = await self.snapshot()
        source = {c.case_id: c for c in load_suite()[1]}
        order = list(range(1, 11))
        rng = random.Random(REVIEW_SEED)
        rng.shuffle(order)
        flips = [False, True] * 5
        rng.shuffle(flips)
        cases, pairs, mapping = [], [], {}
        for i, flip in zip(order, flips, strict=True):
            case = source[replay.cases.IDS[i - 1]]
            template = await run_case(case, {}, "template", load_catalog())
            # Elapsed time is not identity or judgment; exclude it from commitments.
            template = {k: v for k, v in template.items() if k != "elapsed_ms"}
            row = snapshot[i - 1]["row"]
            result = None
            status = "indeterminate" if snapshot[i - 1]["fence"] else "not_started"
            if row:
                if canonical(row[1]) != canonical(self.auto.binding(i)):
                    raise ValueError("automated_binding_conflict")
                if row[3] is not None:
                    try:
                        self.auto.validate_result(row[3], row[1])
                        if row[3]["receipt_sha"] != row[2]:
                            raise ValueError
                        result = row[3]
                        status = result["disposition"]
                    except ValueError:
                        status = "indeterminate"
                else:
                    status = "indeterminate"
            scored = result["scored"] if result else None
            eligible = bool(
                result
                and result["evidence_complete"]
                and scored
                and scored["hard_passed"]
                and scored["quality_eligible"]
                and template["hard_passed"]
                and template["quality_eligible"]
            )
            pair = "pair-" + digest([self.configuration["fingerprint"], i])[:24]
            variants = ["replay", "template"] if flip else ["template", "replay"]
            key = dict(
                ordinal=i,
                public_id=case.case_id,
                pair_id=pair,
                issued=eligible,
                variants=dict(zip(("A", "B"), variants, strict=True)),
                scores={"template": template, "replay": scored},
                replay_disposition=status,
            )
            cases.append(key)
            if eligible:
                outputs = {
                    "template": template["output"]["plan"],
                    "replay": scored["output"]["plan"],
                }
                pairs.append(
                    dict(
                        pair_id=pair,
                        preferences=case.profile.model_dump(mode="json"),
                        variants={
                            label: display(outputs[v]) for label, v in key["variants"].items()
                        },
                    )
                )
                mapping[pair] = i
        content = dict(rubric=RUBRIC_VERSION, pairs=pairs)
        packet = dict(
            version="synthetic-practice-review-packet-v1",
            practice="dummy_only_no_participants",
            packet_id=digest(content),
            content=content,
        )
        value = dict(
            version="synthetic-review-bundle-v1",
            configuration=self.configuration["fingerprint"],
            execution_configuration=self.auto.header["configuration"],
            selection=self.auto.header["selection"],
            automated_snapshot=digest(snapshot),
            rubric=RUBRIC_VERSION,
            packet=packet,
            cases=sorted(cases, key=lambda c: c["ordinal"]),
            mapping=mapping,
            dummy_reviewers=list(REVIEWERS),
        )
        if len(canonical(value)) > LIMIT:
            raise ValueError("review_bundle_bounds")
        return value

    async def issue(self):
        bundle = await self.build()
        async with asyncio.timeout(5):
            c = await self.auto.connection()
            try:
                previous = await (
                    await c.execute("SELECT bundle FROM experiment_e10_packet WHERE slot=1")
                ).fetchone()
                if previous:
                    if canonical(previous[0]) != canonical(bundle):
                        raise ValueError("packet_replacement_denied")
                    await self.check_bundle(previous[0])
                    return previous[0]["packet"]
                replay.cases.sealed.write_exclusive(
                    self.path("packet.claim"), dict(bundle_sha=digest(bundle))
                )
                await c.execute("INSERT INTO experiment_e10_packet VALUES(1,%s)", (Jsonb(bundle),))
                await c.commit()
                return bundle["packet"]
            except Exception:
                raise ValueError("packet_issue_stopped_uncertain") from None
            finally:
                await c.close()

    async def check_bundle(self, bundle):
        self.check_source()
        if (
            bundle["configuration"] != self.configuration["fingerprint"]
            or bundle["execution_configuration"] != self.auto.header["configuration"]
            or bundle["selection"] != self.auto.header["selection"]
            or bundle["rubric"] != RUBRIC_VERSION
            or bundle["dummy_reviewers"] != list(REVIEWERS)
            or bundle["automated_snapshot"] != digest(await self.snapshot())
            or bundle["packet"]["packet_id"] != digest(bundle["packet"]["content"])
        ):
            raise ValueError("review_binding_mismatch")
        path = self.path("packet.claim")
        if path.stat().st_size > 8192 or replay.cases.json_object(path.read_bytes()) != {
            "bundle_sha": digest(bundle)
        }:
            raise ValueError("review_bundle_changed")

    async def load(self):
        self.check_source()
        async with asyncio.timeout(5):
            c = await self.auto.connection(readonly=True)
            try:
                row = await (
                    await c.execute("SELECT bundle FROM experiment_e10_packet WHERE slot=1")
                ).fetchone()
            except Exception:
                raise ValueError("review_storage_unavailable") from None
            finally:
                await c.close()
        if row is None:
            raise ValueError("review_packet_not_issued")
        try:
            await self.check_bundle(row[0])
        except Exception:
            raise ValueError("review_bundle_changed") from None
        return row[0]

    async def export(self):
        return (await self.load())["packet"]

    async def blanks(self):
        b = await self.load()
        forms = []
        for item in b["packet"]["content"]["pairs"]:
            for reviewer in REVIEWERS:
                for label in ("A", "B"):
                    forms.append(
                        dict(
                            version="dummy-blinded-review-v1",
                            evidence="synthetic_dummy_not_human",
                            rubric=RUBRIC_VERSION,
                            packet_id=b["packet"]["packet_id"],
                            pair_id=item["pair_id"],
                            label=label,
                            reviewer=reviewer,
                            judgment_status="pending",
                            ratings=dict.fromkeys(DIMENSIONS),
                            explanation_clarity=None,
                            abstention_reason=None,
                        )
                    )
        return forms

    def validate(self, b, v):
        if v["packet_id"] != b["packet"]["packet_id"] or v["pair_id"] not in b["mapping"]:
            raise ValueError("dummy_submission_binding")
        ordinal = b["mapping"][v["pair_id"]]
        item = b["cases"][ordinal - 1]
        if item["ordinal"] != ordinal or not item["issued"]:
            raise ValueError("dummy_submission_binding")
        source = item["variants"][v["label"]]
        if v["judgment_status"] == "rated_dummy":
            validate_ratings(
                item["scores"][source],
                {**v["ratings"], "explanation_clarity": v["explanation_clarity"]},
            )
        return ordinal

    async def event(self, kind):
        async with asyncio.timeout(5):
            c = await self.auto.connection()
            try:
                await c.execute("INSERT INTO experiment_e10_events(kind) VALUES(%s)", (kind,))
                await c.commit()
            except Exception:
                raise ValueError("review_audit_unavailable") from None
            finally:
                await c.close()

    async def review_rows(self):
        async with asyncio.timeout(5):
            c = await self.auto.connection(readonly=True)
            try:
                rows = await (
                    await c.execute(
                        "SELECT ordinal,label,reviewer,binding,submission_sha,result "
                        "FROM experiment_e10_reviews ORDER BY ordinal,label,reviewer LIMIT 41"
                    )
                ).fetchall()
                events = await (
                    await c.execute("SELECT kind,count(*) FROM experiment_e10_events GROUP BY kind")
                ).fetchall()
            except Exception:
                raise ValueError("review_storage_unavailable") from None
            finally:
                await c.close()
        if len(rows) > 40:
            raise ValueError("review_schedule_overflow")
        return rows, dict(events)

    async def submit(self, raw):
        b = await self.load()
        try:
            v = parse(raw)
            ordinal = self.validate(b, v)
        except Exception:
            await finish_owned(self.event("invalid"))
            raise ValueError("dummy_submission_invalid") from None
        key = (ordinal, v["label"], v["reviewer"])
        slot_binding = digest([b["configuration"], b["selection"], b["packet"]["packet_id"], key])
        submission_sha = digest(v)
        rows, _ = await self.review_rows()
        existing = next((r for r in rows if tuple(r[:3]) == key), None)
        if existing:
            if existing[3] != slot_binding or existing[4] != submission_sha:
                await finish_owned(self.event("conflict"))
                raise ValueError("dummy_judgment_conflict")
            if existing[5] is None:
                raise ValueError("dummy_judgment_indeterminate")
            if canonical(existing[5]) != canonical(v):
                raise ValueError("dummy_judgment_corrupt")
            await finish_owned(self.event("duplicate"))
            return dict(result="duplicate_dummy", evidence="synthetic_not_human")

        async def claim():
            async with asyncio.timeout(5):
                c = await self.auto.connection()
                try:
                    await c.execute(
                        "INSERT INTO experiment_e10_reviews VALUES(%s,%s,%s,%s,%s,NULL)",
                        (*key, slot_binding, submission_sha),
                    )
                    await c.commit()
                finally:
                    await c.close()

        async def finish():
            await (
                self.load()
            )  # Recheck source, packet and first-evidence snapshot after claim wait.
            async with asyncio.timeout(5):
                c = await self.auto.connection()
                try:
                    row = await (
                        await c.execute(
                            "UPDATE experiment_e10_reviews SET result=%s WHERE ordinal=%s "
                            "AND label=%s AND reviewer=%s AND binding=%s AND submission_sha=%s "
                            "AND result IS NULL RETURNING ordinal",
                            (Jsonb(v), *key, slot_binding, submission_sha),
                        )
                    ).fetchone()
                    if row != (ordinal,):
                        raise ValueError("dummy_first_result_conflict")
                    await c.commit()
                finally:
                    await c.close()

        try:
            replay.cases.sealed.write_exclusive(
                self.path(f"review-{ordinal:02}-{v['label']}-{v['reviewer']}.claim"),
                dict(binding=slot_binding, submission_sha=submission_sha),
            )
            await finish_owned(claim())
            await finish_owned(finish())
        except asyncio.CancelledError:
            raise
        except Exception:
            raise ValueError("dummy_import_stopped_uncertain") from None
        return dict(result="accepted_dummy", evidence="synthetic_not_human")

    async def report(self):
        b = await self.load()
        rows, events = await self.review_rows()
        states = dict(
            rated_dummy=0, abstained_dummy=0, indeterminate=0, missing=0, ineligible_pair=0
        )
        ratings = {k: [] for k in DIMENSIONS}
        for item in b["cases"]:
            for label in ("A", "B"):
                for reviewer in REVIEWERS:
                    if not item["issued"]:
                        states["ineligible_pair"] += 1
                        continue
                    key = (item["ordinal"], label, reviewer)
                    row = next((r for r in rows if tuple(r[:3]) == key), None)
                    path = self.path(f"review-{key[0]:02}-{label}-{reviewer}.claim")
                    if row is None:
                        states["indeterminate" if path.exists() else "missing"] += 1
                        continue
                    try:
                        v = parse(canonical(row[5]))
                        if (
                            self.validate(b, v) != key[0]
                            or (v["label"], v["reviewer"]) != key[1:]
                            or row[3]
                            != digest(
                                [b["configuration"], b["selection"], b["packet"]["packet_id"], key]
                            )
                            or row[4] != digest(v)
                        ):
                            raise ValueError
                    except Exception:
                        states["indeterminate"] += 1
                        continue
                    states[v["judgment_status"]] += 1
                    if v["judgment_status"] == "rated_dummy":
                        for k in DIMENSIONS:
                            ratings[k].append(v["ratings"][k])
        replay_counts = {k: 0 for k in replay.STATUSES}
        hard_pass = hard_fail = missing = 0
        for c in b["cases"]:
            replay_counts[c["replay_disposition"]] += 1
            for variant in ("template", "replay"):
                s = c["scores"][variant]
                if s is None or (
                    variant == "replay"
                    and c["replay_disposition"] in ("indeterminate", "interrupted", "not_started")
                ):
                    missing += 1
                elif s["hard_passed"]:
                    hard_pass += 1
                else:
                    hard_fail += 1
        return dict(
            version="synthetic-blinded-report-v1",
            configuration=b["configuration"],
            provenance="local_execution_and_dummy_reviews_not_independent_model_or_human_quality",
            primary_design_pairs=20,
            public_practice_pairs=10,
            unopened_independent_pairs=10,
            automated=dict(
                scheduled_public_outputs=20,
                completed_evaluations=20 - missing,
                hard_passed=hard_pass,
                hard_failed=hard_fail,
                missing_or_indeterminate=missing,
                replay_dispositions=replay_counts,
                template_evidence="actual_local_deterministic_template",
                replay_evidence="actual_local_execution_synthetic_native_responses",
            ),
            dummy_review=dict(
                packet_issues=1,
                planned_slots=40,
                planned_dimension_slots=120,
                issued_pairs=len(b["mapping"]),
                issued_slots=4 * len(b["mapping"]),
                statuses=states,
                events=events,
                valid_submissions=states["rated_dummy"] + states["abstained_dummy"],
                rated_per_dimension={k: len(v) for k, v in ratings.items()},
                dimension_denominators={
                    "planned": 120,
                    "issued": 12 * len(b["mapping"]),
                    **{k: 3 * v for k, v in states.items()},
                },
                dummy_only_means={k: mean(v) if v else None for k, v in ratings.items()},
            ),
            genuine_human=dict(
                judgments=0, planned_reviewers=None, quality_scores=None, evidence="not_collected"
            ),
        )


def import_genuine(*args, **kwargs):
    raise ValueError("genuine_human_import_denied")
