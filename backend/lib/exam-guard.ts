// Guardrail: Meeting AI must not help users cheat on academic exams.
//
// The screen-vision flow (`/api/screen`) runs this quick classifier over the
// screenshot first. If it looks like a graded / proctored academic assessment,
// the route refuses instead of answering. Job interviews, take-home coding
// interviews, practice sites, and work meetings are NOT exams — those are the
// product's intended use and must keep working.

export const EXAM_REFUSAL =
  "🚫 I can't help with this — it looks like an academic exam or graded test. " +
  "Meeting AI won't assist with cheating on exams. I'm here for meetings and interviews."

export const EXAM_CLASSIFIER_PROMPT =
  `Look at this screenshot. Is it an ACADEMIC exam, quiz, graded test, or proctored ` +
  `online assessment that a student is expected to complete on their own — for example: ` +
  `a test/quiz on a school or university platform (Canvas, Blackboard, Moodle, a Google ` +
  `Forms quiz), numbered exam questions with a countdown timer, a standardized test ` +
  `(SAT, GRE, GMAT, TOEFL, etc.), a certification exam under an honor code, or a visible ` +
  `academic-integrity / "no outside help" notice?\n` +
  `Do NOT count job interviews, take-home or live coding interviews, LeetCode/HackerRank ` +
  `practice, documentation, or work meetings as exams.\n` +
  `Answer with exactly one word: YES or NO.`

/**
 * Interpret the classifier's reply. Returns true only on an explicit YES.
 * Anything else — NO, empty, or null — is treated as "not an exam" so a vague
 * or failed classification never blocks legitimate interview/meeting use.
 */
export function isExamVerdict(modelOutput: string | null | undefined): boolean {
  return /\byes\b/i.test(modelOutput ?? '')
}
