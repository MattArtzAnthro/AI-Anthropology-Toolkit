import type * as React from 'react';
type Tone = 'needs' | 'started' | 'done' | 'refused' | 'model';
type CodeTone = 1 | 2 | 3 | 4 | 5 | 6;
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> { variant?: 'primary' | 'secondary' | 'quiet'; reason?: string }
export declare function Button(props: ButtonProps): React.ReactElement;
export interface StatusProps { tone?: Tone; children?: React.ReactNode }
export declare function Status(props: StatusProps): React.ReactElement;
export interface StepProps { n: number; label: React.ReactNode; done?: boolean; children?: React.ReactNode }
export declare function Step(props: StepProps): React.ReactElement;
export interface ChoiceOption { value: string; label: React.ReactNode; description?: React.ReactNode; tone?: CodeTone }
export interface ChoiceGroupProps { legend: React.ReactNode; hint?: React.ReactNode; options: ChoiceOption[]; multiple?: boolean; value?: string | string[] | null; defaultValue?: string | string[] | null; onChange?: (value: any) => void; name?: string; wide?: boolean; hideLegend?: boolean; disabled?: boolean }
export declare function ChoiceGroup(props: ChoiceGroupProps): React.ReactElement;
export interface TextFieldProps extends React.InputHTMLAttributes<HTMLInputElement> { label: React.ReactNode; hint?: React.ReactNode; error?: React.ReactNode; multiline?: boolean }
export declare function TextField(props: TextFieldProps): React.ReactElement;
export interface PassageProps { source?: React.ReactNode; children: React.ReactNode }
export declare function Passage(props: PassageProps): React.ReactElement;
export interface ProvenanceProps { by?: 'model' | 'researcher'; label?: string; children?: React.ReactNode }
export declare function Provenance(props: ProvenanceProps): React.ReactElement;
export interface CodeTagProps { tone?: CodeTone; bare?: boolean; children: React.ReactNode }
export declare function CodeTag(props: CodeTagProps): React.ReactElement;
export interface DecisionCardProps { title: React.ReactNode; eyebrow?: React.ReactNode; state?: 'needs' | 'started' | 'done'; statusLabel?: React.ReactNode; result?: React.ReactNode; doneLabel?: React.ReactNode; onChange?: () => void; id?: string; children?: React.ReactNode }
export declare function DecisionCard(props: DecisionCardProps): React.ReactElement;
export interface NoticeProps { tone?: 'info' | 'refusal' | 'done'; title: React.ReactNode; children?: React.ReactNode }
export declare function Notice(props: NoticeProps): React.ReactElement;
export interface TallyProps { left: number; total: number; noun?: string; onNext?: () => void; sticky?: boolean; doneText?: string; /** Ignored when sticky: a sticky tally is one row. */ children?: React.ReactNode }
export declare function Tally(props: TallyProps): React.ReactElement;
/** One segment per item in a queue: the first `done` are decided, `current` (an index) is the one that needs you. */
export interface ProgressProps { total: number; done: number; current?: number; label?: string }
export declare function Progress(props: ProgressProps): React.ReactElement;
export interface Stage { id: string; label: React.ReactNode; note?: React.ReactNode }
export interface StagesProps { stages: Stage[]; current: string; onSelect?: (id: string) => void; label?: string }
export declare function Stages(props: StagesProps): React.ReactElement;
export interface TableColumn { key: string; label: React.ReactNode; numeric?: boolean }
export interface TableProps { caption?: React.ReactNode; columns: TableColumn[]; rows: Array<Record<string, React.ReactNode> & { id?: string }> }
export declare function Table(props: TableProps): React.ReactElement;
export interface BylineProps { version?: string; full?: boolean }
export declare function Byline(props: BylineProps): React.ReactElement;
declare global { interface Window { AAT: { Button: typeof Button; Status: typeof Status; Step: typeof Step; ChoiceGroup: typeof ChoiceGroup; TextField: typeof TextField; Passage: typeof Passage; Provenance: typeof Provenance; CodeTag: typeof CodeTag; DecisionCard: typeof DecisionCard; Notice: typeof Notice; Tally: typeof Tally; Progress: typeof Progress; Stages: typeof Stages; Table: typeof Table; Byline: typeof Byline } } }
