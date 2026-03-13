import React, { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { motion } from "framer-motion";
import { Sigma, Braces, ArrowRightLeft, Binary, FunctionSquare, Calculator } from "lucide-react";

type TensorKind = "scalar" | "vector" | "covector" | "tensor2";
type Variance = "+" | "-";

type TensorValue = number | number[] | number[][];

type TokenType =
  | "number"
  | "identifier"
  | "plus"
  | "star"
  | "contract"
  | "lparen"
  | "rparen"
  | "comma"
  | "semicolon"
  | "eof";

interface Token {
  type: TokenType;
  value: string;
  pos: number;
}

type ASTNode =
  | { type: "TensorLiteral"; raw: string; tensor: TensorExpr }
  | { type: "BinaryExpr"; op: "+" | "*" | "@"; left: ASTNode; right: ASTNode };

function lex(input: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;

  const push = (type: TokenType, value: string, pos: number) => {
    tokens.push({ type, value, pos });
  };

  while (i < input.length) {
    const ch = input[i];

    if (/\s/.test(ch)) {
      i += 1;
      continue;
    }

    if (/[0-9]/.test(ch) || (ch === "-" && /[0-9]/.test(input[i + 1] || ""))) {
      const start = i;
      i += 1;
      while (i < input.length && /[0-9.]/.test(input[i])) i += 1;
      push("number", input.slice(start, i), start);
      continue;
    }

    if (/[A-Za-z_]/.test(ch)) {
      const start = i;
      i += 1;
      while (i < input.length && /[A-Za-z0-9_*]/.test(input[i])) i += 1;
      push("identifier", input.slice(start, i), start);
      continue;
    }

    if (ch === "+") push("plus", ch, i);
    else if (ch === "*") push("star", ch, i);
    else if (ch === "@") push("contract", ch, i);
    else if (ch === "(") push("lparen", ch, i);
    else if (ch === ")") push("rparen", ch, i);
    else if (ch === ",") push("comma", ch, i);
    else if (ch === ";") push("semicolon", ch, i);
    else throw new Error(`Unexpected character '${ch}' at position ${i}.`);

    i += 1;
  }

  push("eof", "", input.length);
  return tokens;
}

class Parser {
  private tokens: Token[];
  private index = 0;

  constructor(tokens: Token[]) {
    this.tokens = tokens;
  }

  private current(): Token {
    return this.tokens[this.index];
  }

  private advance(): Token {
    const token = this.tokens[this.index];
    this.index += 1;
    return token;
  }

  private expect(type: TokenType, message: string): Token {
    const token = this.current();
    if (token.type !== type) {
      throw new Error(`${message} Found '${token.value}' at position ${token.pos}.`);
    }
    return this.advance();
  }

  parse(): ASTNode {
    const expr = this.parseAdditive();
    if (this.current().type !== "eof") {
      throw new Error(
        `Unexpected token '${this.current().value}' at position ${this.current().pos}.`
      );
    }
    return expr;
  }

  private parseAdditive(): ASTNode {
    let node = this.parseMultiplicative();

    while (this.current().type === "plus") {
      this.advance();
      node = {
        type: "BinaryExpr",
        op: "+",
        left: node,
        right: this.parseMultiplicative(),
      };
    }

    return node;
  }

  private parseMultiplicative(): ASTNode {
    let node = this.parsePrimary();

    while (this.current().type === "star" || this.current().type === "contract") {
      const op = this.advance();

      node = {
        type: "BinaryExpr",
        op: op.type === "star" ? "*" : "@",
        left: node,
        right: this.parsePrimary(),
      };
    }

    return node;
  }

  private parsePrimary(): ASTNode {
    const token = this.current();

    if (token.type === "number") {
      this.advance();
      return {
        type: "TensorLiteral",
        raw: token.value,
        tensor: scalar(Number(token.value)),
      };
    }

    if (token.type === "identifier") {
      return this.parseTensorConstructor();
    }

    if (token.type === "lparen") {
      this.advance();
      const expr = this.parseAdditive();
      this.expect("rparen", "Missing closing parenthesis.");
      return expr;
    }

    throw new Error(`Unexpected token '${token.value}' at position ${token.pos}.`);
  }

  private parseTensorConstructor(): ASTNode {
    const name = this.expect("identifier", "Expected tensor constructor.").value;

    if (!/^(v|cv|m)$/i.test(name)) {
      throw new Error(`Unknown constructor '${name}'. Use v(...), cv(...), or m(...).`);
    }

    this.expect("lparen", `Expected '(' after ${name}.`);

    if (/^v$/i.test(name) || /^cv$/i.test(name)) {
      const values: number[] = [];

      while (this.current().type !== "rparen") {
        const tok = this.expect("number", `Expected numeric component in ${name}(...).`);
        values.push(Number(tok.value));

        if (this.current().type === "comma") {
          this.advance();
        } else {
          break;
        }
      }

      this.expect("rparen", `Expected ')' to close ${name}(...).`);

      return {
        type: "TensorLiteral",
        raw: `${name}(${values.join(",")})`,
        tensor: /^v$/i.test(name) ? vector(values) : covector(values),
      };
    }

    const rows: number[][] = [];
    let row: number[] = [];

    while (this.current().type !== "rparen") {
      const tok = this.expect("number", "Expected numeric matrix component in m(...).");
      row.push(Number(tok.value));

      if (this.current().type === "comma") {
        this.advance();
      } else if (this.current().type === "semicolon") {
        this.advance();
        rows.push(row);
        row = [];
      } else {
        break;
      }
    }

    rows.push(row);
    this.expect("rparen", "Expected ')' to close m(...).");

    return {
      type: "TensorLiteral",
      raw: `m(${rows.map((r) => r.join(",")).join(";")})`,
      tensor: tensor2(rows),
    };
  }
}

function astToString(node: ASTNode): string {
  if (node.type === "TensorLiteral") return node.raw;
  return `(${astToString(node.left)} ${node.op} ${astToString(node.right)})`;
}

function astToTensorExpression(node: ASTNode): string {
  if (node.type === "TensorLiteral") return node.tensor.display;
  return `(${astToTensorExpression(node.left)} ${node.op} ${astToTensorExpression(node.right)})`;
}

function evaluateAST(node: ASTNode, logs: string[]): TensorExpr {
  if (node.type === "TensorLiteral") {
    logs.push(
      `Literal '${node.raw}' => ${tensorTypeString(node.tensor)} with value ${node.tensor.display}.`
    );
    return node.tensor;
  }

  const left = evaluateAST(node.left, logs);
  const right = evaluateAST(node.right, logs);

  logs.push(`Apply '${node.op}' to ${left.display} and ${right.display}. ${explainBinary(node.op)}`);

  if (node.op === "+") {
    const out = addTensors(left, right);
    logs.push(`Result of addition => ${tensorTypeString(out)} with value ${out.display}.`);
    return out;
  }

  if (node.op === "*") {
    const out = tensorProduct(left, right);
    logs.push(
      `Result of tensor product/scaling => ${tensorTypeString(out)} with value ${out.display}.`
    );
    return out;
  }

  const out = contract(left, right);
  logs.push(`Result of contraction => ${tensorTypeString(out)} with value ${out.display}.`);
  return out;
}

function evaluateExpression(input: string): EvalResult {
  const normalizedInput = input.trim();
  const logs: string[] = [];

  try {
    const tokens = lex(normalizedInput);
    logs.push(`Lexed input into ${tokens.filter((t) => t.type !== "eof").length} symbolic tokens.`);

    const parser = new Parser(tokens);
    const ast = parser.parse();

    logs.push(`Parsed expression tree => ${astToString(ast)}.`);

    const result = evaluateAST(ast, logs);

    return {
      ordinaryInput: input,
      normalizedInput,
      astLike: astToString(ast),
      tensorExpression: astToTensorExpression(ast),
      result,
      logs,
    };
  } catch (error) {
    return {
      ordinaryInput: input,
      normalizedInput,
      astLike: "—",
      tensorExpression: "—",
      result: null,
      logs,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

interface TensorExpr {
  kind: TensorKind;
  rank: number;
  spaces: string[];
  variances: Variance[];
  value: TensorValue;
  display: string;
  explanation: string;
}

interface EvalResult {
  ordinaryInput: string;
  normalizedInput: string;
  astLike: string;
  tensorExpression: string;
  result: TensorExpr | null;
  logs: string[];
  error?: string;
}

function isNumberToken(token: string): boolean {
  return /^-?\d+(\.\d+)?$/.test(token.trim());
}

function scalar(n: number): TensorExpr {
  return {
    kind: "scalar",
    rank: 0,
    spaces: [],
    variances: [],
    value: n,
    display: `${n}`,
    explanation: `Scalar ${n} is interpreted as a rank-0 tensor.`
  };
}

function vector(xs: number[], space = "V"): TensorExpr {
  return {
    kind: "vector",
    rank: 1,
    spaces: [space],
    variances: ["+"],
    value: xs,
    display: `[${xs.join(", ")}]^${space}`,
    explanation: `Vector in ${space} with one contravariant index.`
  };
}

function covector(xs: number[], space = "V*"): TensorExpr {
  return {
    kind: "covector",
    rank: 1,
    spaces: [space],
    variances: ["-"],
    value: xs,
    display: `[${xs.join(", ")}]_${space}`,
    explanation: `Covector in ${space} with one covariant index.`
  };
}

function tensor2(xs: number[][], spaces = ["V", "V*"]): TensorExpr {
  return {
    kind: "tensor2",
    rank: 2,
    spaces,
    variances: ["+", "-"],
    value: xs,
    display: `[[${xs.map((r) => r.join(", ")).join("], [")}]]`,
    explanation: `Rank-2 tensor with one upper and one lower index.`
  };
}

function tensorTypeString(t: TensorExpr): string {
  if (t.rank === 0) return "T[] = scalar";
  const idx = t.variances
    .map((v, i) => `${String.fromCharCode(97 + i)}${v}:${t.spaces[i]}`)
    .join(", ");
  return `T[${idx}] (rank ${t.rank})`;
}

function addTensors(a: TensorExpr, b: TensorExpr): TensorExpr {
  if (a.kind !== b.kind || a.rank !== b.rank) {
    throw new Error(`Addition requires identical tensor type. Got ${a.kind} and ${b.kind}.`);
  }
  if (a.kind === "scalar") return scalar((a.value as number) + (b.value as number));
  if (a.kind === "vector") {
    const av = a.value as number[];
    const bv = b.value as number[];
    if (av.length !== bv.length) throw new Error("Vector addition requires equal dimension.");
    return vector(av.map((x, i) => x + bv[i]), a.spaces[0]);
  }
  if (a.kind === "covector") {
    const av = a.value as number[];
    const bv = b.value as number[];
    if (av.length !== bv.length) throw new Error("Covector addition requires equal dimension.");
    return covector(av.map((x, i) => x + bv[i]), a.spaces[0]);
  }
  const am = a.value as number[][];
  const bm = b.value as number[][];
  if (am.length !== bm.length || am[0].length !== bm[0].length) {
    throw new Error("Rank-2 tensor addition requires equal shape.");
  }
  return tensor2(am.map((r, i) => r.map((x, j) => x + bm[i][j])), a.spaces);
}

function tensorProduct(a: TensorExpr, b: TensorExpr): TensorExpr {
  if (a.kind === "scalar") {
    const s = a.value as number;
    return scaleTensor(b, s);
  }
  if (b.kind === "scalar") {
    const s = b.value as number;
    return scaleTensor(a, s);
  }
  if (a.kind === "vector" && b.kind === "covector") {
    const av = a.value as number[];
    const bv = b.value as number[];
    return tensor2(av.map((x) => bv.map((y) => x * y)), [a.spaces[0], b.spaces[0]]);
  }
  throw new Error("Tensor product is implemented here for scalar×anything and vector⊗covector.");
}

function contract(a: TensorExpr, b: TensorExpr): TensorExpr {
  if (a.kind === "covector" && b.kind === "vector") {
    const av = a.value as number[];
    const bv = b.value as number[];
    if (av.length !== bv.length) throw new Error("Contraction requires matching dimension.");
    return scalar(av.reduce((sum, x, i) => sum + x * bv[i], 0));
  }
  if (a.kind === "tensor2" && b.kind === "vector") {
    const m = a.value as number[][];
    const v = b.value as number[];
    if (m[0].length !== v.length) throw new Error("Tensor-vector contraction requires matching dimensions.");
    return vector(m.map((row) => row.reduce((sum, x, i) => sum + x * v[i], 0)), a.spaces[0]);
  }
  throw new Error("Contraction is implemented here for covector·vector and rank2·vector.");
}

function scaleTensor(t: TensorExpr, s: number): TensorExpr {
  if (t.kind === "scalar") return scalar((t.value as number) * s);
  if (t.kind === "vector") return vector((t.value as number[]).map((x) => x * s), t.spaces[0]);
  if (t.kind === "covector") return covector((t.value as number[]).map((x) => x * s), t.spaces[0]);
  return tensor2((t.value as number[][]).map((r) => r.map((x) => x * s)), t.spaces);
}

function parseTensorLiteral(raw: string): TensorExpr {
  const t = raw.trim();
  if (isNumberToken(t)) return scalar(Number(t));
  if (/^v\(([-\d.,\s]+)\)$/i.test(t)) {
    const inside = t.slice(2, -1);
    return vector(inside.split(",").map((x) => Number(x.trim())));
  }
  if (/^cv\(([-\d.,\s]+)\)$/i.test(t)) {
    const inside = t.slice(3, -1);
    return covector(inside.split(",").map((x) => Number(x.trim())));
  }
  if (/^m\((.+)\)$/i.test(t)) {
    const inside = t.slice(2, -1);
    const rows = inside.split(";").map((row) => row.split(",").map((x) => Number(x.trim())));
    return tensor2(rows);
  }
  throw new Error(`Could not parse token '${raw}'. Use forms like 2, v(1,2), cv(3,4), m(1,2;3,4).`);
}

function tokenize(expr: string): string[] {
  return expr
    .replace(/\s+/g, "")
    .replace(/([+*@])/g, " $1 ")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
}

function explainBinary(op: string): string {
  switch (op) {
    case "+":
      return "Addition in tensor-standard math is valid only for identical tensor types.";
    case "*":
      return "* is interpreted as tensor product when both operands are tensors, or scalar scaling when one operand is rank-0.";
    case "@":
      return "@ is explicit contraction. Example: cv(1,2) @ v(3,4).";
    default:
      return "Unknown operator.";
  }
}

function evaluateExpression(input: string): EvalResult {
  const normalizedInput = input.trim();
  const logs: string[] = [];
  try {
    const tokens = tokenize(normalizedInput);
    if (tokens.length === 0) throw new Error("Enter an expression.");
    let current = parseTensorLiteral(tokens[0]);
    logs.push(`Parsed '${tokens[0]}' as ${tensorTypeString(current)} with value ${current.display}.`);

    const astParts = [tokens[0]];
    const tensorParts = [current.display];

    for (let i = 1; i < tokens.length; i += 2) {
      const op = tokens[i];
      const rhsToken = tokens[i + 1];
      if (!rhsToken) throw new Error("Expression ended unexpectedly.");
      const rhs = parseTensorLiteral(rhsToken);
      logs.push(`Parsed '${rhsToken}' as ${tensorTypeString(rhs)} with value ${rhs.display}.`);
      logs.push(explainBinary(op));

      if (op === "+") current = addTensors(current, rhs);
      else if (op === "*") current = tensorProduct(current, rhs);
      else if (op === "@") current = contract(current, rhs);
      else throw new Error(`Unsupported operator '${op}'.`);

      astParts.push(op, rhsToken);
      tensorParts.push(op, rhs.display);
      logs.push(`Intermediate result => ${tensorTypeString(current)} with value ${current.display}.`);
    }

    return {
      ordinaryInput: input,
      normalizedInput,
      astLike: astParts.join(" "),
      tensorExpression: tensorParts.join(" "),
      result: current,
      logs
    };
  } catch (error) {
    return {
      ordinaryInput: input,
      normalizedInput,
      astLike: "—",
      tensorExpression: "—",
      result: null,
      logs,
      error: error instanceof Error ? error.message : "Unknown error"
    };
  }
}

const examples = [
  {
    label: "Ordinary arithmetic",
    input: "1 + 2",
    meaning: "Treats 1 and 2 as rank-0 tensors, so 1 + 2 = 3 is tensor-valid scalar addition.",
  },
  {
    label: "Grouped scalar/vector",
    input: "(1 + 2) * v(3,4)",
    meaning: "Parentheses are now parsed symbolically before evaluation.",
  },
  {
    label: "Covector contracts with vector",
    input: "cv(1,2) @ v(3,4)",
    meaning: "Explicit contraction returns a scalar: 1·3 + 2·4 = 11.",
  },
  {
    label: "Vector outer covector",
    input: "v(2,1) * cv(5,7)",
    meaning: "Tensor product returns a rank-2 tensor.",
  },
  {
    label: "Nested symbolic expression",
    input: "(cv(1,2) @ v(3,4)) + 5",
    meaning: "A contraction can now feed a later symbolic addition.",
  },
  {
    label: "Matrix acting on vector",
    input: "m(1,2;3,4) @ v(5,6)",
    meaning: "A simple rank-2 by rank-1 contraction.",
  },
];

function TypeBadge({ tensor }: { tensor: TensorExpr }) {
  return (
    <div className="flex flex-wrap gap-2">
      <Badge variant="secondary">kind: {tensor.kind}</Badge>
      <Badge variant="secondary">rank: {tensor.rank}</Badge>
      {tensor.spaces.length > 0 && <Badge variant="secondary">spaces: {tensor.spaces.join(", ")}</Badge>}
      {tensor.variances.length > 0 && <Badge variant="secondary">variance: {tensor.variances.join(" ")}</Badge>}
    </div>
  );
}

export default function TensorStandardMathCalculator() {
  const [input, setInput] = useState("1 + 2");
  const [conversionMode, setConversionMode] = useState("strict");

  const result = useMemo(() => evaluateExpression(input), [input]);

  const conversionNotes = useMemo(() => {
    if (conversionMode === "strict") {
      return [
        "Plain numerals are auto-promoted to rank-0 tensors.",
        "'+' requires identical tensor type.",
        "'*' means tensor product unless one side is scalar, in which case it means scaling.",
        "'@' means contraction and is always explicit."
      ];
    }
    return [
      "Educational mode explains ordinary arithmetic as special cases of tensor-standard math.",
      "1 + 2 is displayed as T[] + T[] → T[].",
      "Vector and covector literals expose rank and variance.",
      "The goal is not just to compute, but to reveal structure."
    ];
  }, [conversionMode]);

  return (
    <div className="min-h-screen bg-background p-6 md:p-10">
      <div className="mx-auto max-w-7xl space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="grid gap-4 md:grid-cols-[1.5fr_1fr]"
        >
          <Card className="rounded-3xl shadow-sm border-border/60">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="rounded-2xl border p-2">
                  <Calculator className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle className="text-2xl">Tensor Standard Math Calculator</CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    Ordinary arithmetic reinterpreted as typed tensor operations.
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-[1fr_180px]">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Examples: 1 + 2, 2 * v(3,4), cv(1,2) @ v(3,4)"
                  className="h-12 rounded-2xl text-base"
                />
                <Select value={conversionMode} onValueChange={setConversionMode}>
                  <SelectTrigger className="h-12 rounded-2xl">
                    <SelectValue placeholder="Conversion mode" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="strict">Strict</SelectItem>
                    <SelectItem value="educational">Educational</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-wrap gap-2">
                {examples.map((example) => (
                  <Button
                    key={example.input}
                    variant="outline"
                    className="rounded-2xl"
                    onClick={() => setInput(example.input)}
                  >
                    {example.label}
                  </Button>
                ))}
              </div>

              <Alert className="rounded-2xl">
                <AlertDescription>
                  Accepted literals: plain numbers like <code>2</code>, vectors like <code>v(1,2)</code>, covectors like <code>cv(3,4)</code>,
                  and rank-2 tensors like <code>m(1,2;3,4)</code>.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>

          <Card className="rounded-3xl shadow-sm border-border/60">
            <CardHeader>
              <CardTitle className="text-lg">Conversion rules</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              {conversionNotes.map((note) => (
                <div key={note} className="rounded-2xl border p-3">{note}</div>
              ))}
            </CardContent>
          </Card>
        </motion.div>

        <Tabs defaultValue="result" className="space-y-4">
          <TabsList className="rounded-2xl">
            <TabsTrigger value="result">Result</TabsTrigger>
            <TabsTrigger value="trace">Trace</TabsTrigger>
            <TabsTrigger value="theory">Theory</TabsTrigger>
          </TabsList>

          <TabsContent value="result" className="space-y-4">
            <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
              <Card className="rounded-3xl shadow-sm border-border/60">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg"><Binary className="h-4 w-4" /> Interpretation</CardTitle>
                </CardHeader>
                <CardContent className="space-y-5">
                  <div className="rounded-2xl border p-4">
                    <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1">Input</div>
                    <div className="font-mono text-lg">{result.normalizedInput || "—"}</div>
                  </div>
                  <div className="rounded-2xl border p-4">
                    <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1">Tensor-form expression</div>
                    <div className="font-mono text-lg break-words">{result.tensorExpression}</div>
                  </div>
                  <div className="rounded-2xl border p-4">
                    <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1">Symbolic parse tree</div>
                    <div className="font-mono text-lg">{result.astLike}</div>
                  </div>
                </CardContent>
              </Card>

              <Card className="rounded-3xl shadow-sm border-border/60">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg"><Sigma className="h-4 w-4" /> Output</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {result.error ? (
                    <Alert className="rounded-2xl">
                      <AlertDescription>{result.error}</AlertDescription>
                    </Alert>
                  ) : result.result ? (
                    <>
                      <div className="rounded-2xl border p-4">
                        <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1">Result value</div>
                        <div className="font-mono text-2xl">{result.result.display}</div>
                      </div>
                      <TypeBadge tensor={result.result} />
                      <div className="rounded-2xl border p-4 text-sm text-muted-foreground">
                        {result.result.explanation}
                      </div>
                    </>
                  ) : null}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="trace">
            <Card className="rounded-3xl shadow-sm border-border/60">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg"><ArrowRightLeft className="h-4 w-4" /> Evaluation trace</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {result.logs.length === 0 ? (
                    <div className="text-sm text-muted-foreground">No trace yet.</div>
                  ) : (
                    result.logs.map((log, i) => (
                      <motion.div
                        key={`${log}-${i}`}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.03 }}
                        className="rounded-2xl border p-3 text-sm"
                      >
                        {log}
                      </motion.div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="theory">
            <div className="grid gap-4 md:grid-cols-3">
              <Card className="rounded-3xl shadow-sm border-border/60">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg"><Braces className="h-4 w-4" /> Core rules</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-muted-foreground">
                  <div className="rounded-2xl border p-3">Scalars are rank-0 tensors.</div>
                  <div className="rounded-2xl border p-3">Addition requires identical tensor type.</div>
                  <div className="rounded-2xl border p-3">Tensor product combines structure without collapsing it.</div>
                  <div className="rounded-2xl border p-3">Contraction is explicit and dimension-aware.</div>
                </CardContent>
              </Card>

              <Card className="rounded-3xl shadow-sm border-border/60">
                <CardHeader>
                  <CardTitle className="text-lg">What 1 + 2 means here</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-muted-foreground">
                  <div className="rounded-2xl border p-3">1 is promoted to T[] with value 1.</div>
                  <div className="rounded-2xl border p-3">2 is promoted to T[] with value 2.</div>
                  <div className="rounded-2xl border p-3">T[] + T[] is valid because both are rank-0.</div>
                  <div className="rounded-2xl border p-3">The result 3 is also T[]: scalar arithmetic is a special case of tensor arithmetic.</div>
                </CardContent>
              </Card>

              <Card className="rounded-3xl shadow-sm border-border/60">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg"><FunctionSquare className="h-4 w-4" /> Next expansions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-muted-foreground">
                  <div className="rounded-2xl border p-3">Add named spaces and explicit variance checking.</div>
                  <div className="rounded-2xl border p-3">Support symbolic indices like T[a+, b-].</div>
                  <div className="rounded-2xl border p-3">Introduce metrics for raising and lowering.</div>
                  <div className="rounded-2xl border p-3">Add covariant derivatives and invariant checks.</div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
