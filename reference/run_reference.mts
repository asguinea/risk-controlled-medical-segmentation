import { readFileSync } from "node:fs";
import { calibrateBoundedMonotoneExpectationCrcV1 } from "./bounded-monotone-expectation-crc-v1.ts";

const cases = JSON.parse(readFileSync(0, "utf8"));
process.stdout.write(JSON.stringify(cases.map(calibrateBoundedMonotoneExpectationCrcV1)));
