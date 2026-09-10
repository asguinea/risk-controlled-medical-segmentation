export const BOUNDED_MONOTONE_EXPECTATION_CRC_V1 = "BOUNDED_MONOTONE_EXPECTATION_CRC_V1" as const;

export interface ExactRationalInputV1 {
  readonly numerator: string;
  readonly denominator: string;
}

export interface BoundedLossCandidateV1 {
  readonly lambda: number;
  readonly patient_losses: readonly ExactRationalInputV1[];
}

export interface BoundedMonotoneExpectationCrcV1Input {
  readonly method_profile_id: typeof BOUNDED_MONOTONE_EXPECTATION_CRC_V1;
  readonly alpha: ExactRationalInputV1;
  readonly candidates: readonly BoundedLossCandidateV1[];
}

export interface BoundedMonotoneExpectationCrcV1Success {
  readonly ok: true;
  readonly method_profile_id: typeof BOUNDED_MONOTONE_EXPECTATION_CRC_V1;
  readonly certified: boolean;
  readonly selected_lambda: number;
  readonly fallback_state: "NONE" | "ALL_LABELS";
  readonly calibration_patient_count: number;
  readonly candidate_count: number;
  readonly empirical_total_loss: string;
  readonly empirical_risk: string;
  readonly adjusted_risk: string;
}

export interface BoundedMonotoneExpectationCrcV1Failure {
  readonly ok: false;
  readonly method_profile_id: typeof BOUNDED_MONOTONE_EXPECTATION_CRC_V1;
  readonly reason_codes: readonly string[];
}

export type BoundedMonotoneExpectationCrcV1Result =
  BoundedMonotoneExpectationCrcV1Success | BoundedMonotoneExpectationCrcV1Failure;

interface Fraction {
  readonly numerator: bigint;
  readonly denominator: bigint;
}

interface NormalizedCandidate {
  readonly lambda: number;
  readonly losses: readonly Fraction[];
}

export function calibrateBoundedMonotoneExpectationCrcV1(
  input: BoundedMonotoneExpectationCrcV1Input
): BoundedMonotoneExpectationCrcV1Result {
  const issues: string[] = [];
  if (input.method_profile_id !== BOUNDED_MONOTONE_EXPECTATION_CRC_V1)
    issues.push("METHOD_PROFILE_MISMATCH");
  const alpha = parseFraction(input.alpha, issues, "INVALID_ALPHA");
  if (alpha && (compare(alpha, zero()) <= 0 || compare(alpha, one()) >= 0))
    issues.push("INVALID_ALPHA");
  if (!Array.isArray(input.candidates) || input.candidates.length === 0)
    issues.push("EMPTY_CANDIDATE_SET");

  const normalized: NormalizedCandidate[] = [];
  let patientCount: number | undefined;
  for (const candidate of input.candidates ?? []) {
    if (!Number.isFinite(candidate.lambda) || candidate.lambda < 0 || candidate.lambda > 1) {
      issues.push("INVALID_LAMBDA");
      continue;
    }
    if (!Array.isArray(candidate.patient_losses) || candidate.patient_losses.length === 0) {
      issues.push("EMPTY_CALIBRATION_POPULATION");
      continue;
    }
    patientCount ??= candidate.patient_losses.length;
    if (candidate.patient_losses.length !== patientCount) issues.push("INCONSISTENT_PATIENT_COUNT");
    const losses = candidate.patient_losses
      .map((loss) => parseFraction(loss, issues, "INVALID_BOUNDED_LOSS"))
      .filter((loss): loss is Fraction => loss !== undefined);
    if (losses.some((loss) => compare(loss, zero()) < 0 || compare(loss, one()) > 0))
      issues.push("INVALID_BOUNDED_LOSS");
    normalized.push({ lambda: normalizeZero(candidate.lambda), losses });
  }
  normalized.sort((left, right) => left.lambda - right.lambda);
  if (new Set(normalized.map(({ lambda }) => lambda)).size !== normalized.length)
    issues.push("DUPLICATE_LAMBDA");
  if (normalized[0]?.lambda !== 0 || normalized.at(-1)?.lambda !== 1)
    issues.push("MISSING_ZERO_OR_ONE_ENDPOINT");
  for (let index = 1; index < normalized.length; index += 1) {
    const previous = normalized[index - 1]!;
    const current = normalized[index]!;
    if (previous.losses.length !== current.losses.length) continue;
    if (current.losses.some((loss, patient) => compare(loss, previous.losses[patient]!) > 0))
      issues.push("NON_MONOTONE_PATIENT_LOSS");
  }
  const endpoint = normalized.at(-1);
  if (endpoint?.losses.some((loss) => compare(loss, zero()) !== 0))
    issues.push("NONCONSERVATIVE_ALL_LABEL_ENDPOINT");
  if (issues.length > 0 || !alpha || patientCount === undefined)
    return Object.freeze({
      ok: false,
      method_profile_id: BOUNDED_MONOTONE_EXPECTATION_CRC_V1,
      reason_codes: Object.freeze([...new Set(issues)].sort())
    });

  const states = normalized.map((candidate) => {
    const total = candidate.losses.reduce(add, zero());
    const adjusted = divide(add(total, one()), fromInteger(BigInt(patientCount + 1)));
    return { ...candidate, total, adjusted, admissible: compare(adjusted, alpha) <= 0 };
  });
  const selected = states.find(({ admissible }) => admissible);
  const effective = selected ?? states.at(-1)!;
  const empirical = divide(effective.total, fromInteger(BigInt(patientCount)));
  return Object.freeze({
    ok: true,
    method_profile_id: BOUNDED_MONOTONE_EXPECTATION_CRC_V1,
    certified: selected !== undefined,
    selected_lambda: effective.lambda,
    fallback_state: selected === undefined ? "ALL_LABELS" : "NONE",
    calibration_patient_count: patientCount,
    candidate_count: states.length,
    empirical_total_loss: format(effective.total),
    empirical_risk: format(empirical),
    adjusted_risk: format(effective.adjusted)
  });
}

function parseFraction(
  input: ExactRationalInputV1,
  issues: string[],
  code: string
): Fraction | undefined {
  try {
    if (!/^-?[0-9]+$/.test(input.numerator) || !/^[0-9]+$/.test(input.denominator))
      throw new Error("invalid rational syntax");
    return fraction(BigInt(input.numerator), BigInt(input.denominator));
  } catch {
    issues.push(code);
    return undefined;
  }
}

function fraction(numerator: bigint, denominator: bigint): Fraction {
  if (denominator <= 0n) throw new Error("denominator must be positive");
  const divisor = gcd(numerator < 0n ? -numerator : numerator, denominator);
  return { numerator: numerator / divisor, denominator: denominator / divisor };
}

function zero(): Fraction {
  return { numerator: 0n, denominator: 1n };
}

function one(): Fraction {
  return { numerator: 1n, denominator: 1n };
}

function fromInteger(value: bigint): Fraction {
  return { numerator: value, denominator: 1n };
}

function add(left: Fraction, right: Fraction): Fraction {
  return fraction(
    left.numerator * right.denominator + right.numerator * left.denominator,
    left.denominator * right.denominator
  );
}

function divide(left: Fraction, right: Fraction): Fraction {
  if (right.numerator === 0n) throw new Error("division by zero");
  const sign = right.numerator < 0n ? -1n : 1n;
  return fraction(
    left.numerator * right.denominator * sign,
    left.denominator * right.numerator * sign
  );
}

function compare(left: Fraction, right: Fraction): number {
  const difference = left.numerator * right.denominator - right.numerator * left.denominator;
  return difference < 0n ? -1 : difference > 0n ? 1 : 0;
}

function format(value: Fraction): string {
  return `${value.numerator}/${value.denominator}`;
}

function gcd(left: bigint, right: bigint): bigint {
  let a = left;
  let b = right;
  while (b !== 0n) [a, b] = [b, a % b];
  return a === 0n ? 1n : a;
}

function normalizeZero(value: number): number {
  return Object.is(value, -0) ? 0 : value;
}
