// Generated from contracts/openapi.json. Do not edit.
import type { components } from "./api.generated.js";
export function validateEvent(data: unknown): data is components["schemas"]["StreamEvent"];
export function validateProfile(data: unknown): data is components["schemas"]["SavedProfile"];
export function validateExercise(data: unknown): data is components["schemas"]["CatalogRecord"];
export function validateError(data: unknown): data is components["schemas"]["ApiError"];
export function validateApproval(data: unknown): data is components["schemas"]["ApprovalResult"];
export function validateSavedPlan(data: unknown): data is components["schemas"]["SavedPlan"];
export function validateSessionRecord(data: unknown): data is components["schemas"]["SessionRecord"];
export function validateSubmission(data: unknown): data is components["schemas"]["SessionSubmission"];
export function validateSubmissionError(data: unknown): data is components["schemas"]["SubmissionError"];
export const MAX_FRAME_BYTES: number;
export const MAX_EVENTS: number;
