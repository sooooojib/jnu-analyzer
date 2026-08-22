import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Copy,
  Check,
  ExternalLink,
  UploadCloud,
  FileText,
  X,
  Loader2,
  Cpu,
  GraduationCap,
  BookOpen,
  Building2
} from 'lucide-react';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Card } from '../common/Card';
import { api } from '../../api/endpoints';

export interface ClaudeAiAssistantProps {
  onMarkdownSubmit: (markdownText: string, filename?: string) => Promise<void>;
  isProcessing?: boolean;
  navigationTabs?: React.ReactNode;
}

interface AiTool {
  name: string;
  model: string;
  url: string;
  description: string;
  badge: string;
  color: string;
}

export const ClaudeAiAssistant: React.FC<ClaudeAiAssistantProps> = ({
  onMarkdownSubmit,
  isProcessing = false,
  navigationTabs,
}) => {
  const [promptText, setPromptText] = useState<string>('');
  const [aiTools, setAiTools] = useState<AiTool[]>([
    {
      name: 'Google AI Studio',
      model: 'Gemini 1.5 Pro / 2.0 Pro (Latest)',
      url: 'https://aistudio.google.com',
      description: 'Recommended for Multi-Page Merging: Upload 2–10+ photos at once with massive 2M token context window.',
      badge: 'Best for Multi-Page',
      color: 'amber',
    },
    {
      name: 'Claude AI',
      model: 'Claude 3.5 Sonnet / 3.7',
      url: 'https://claude.ai',
      description: 'Clinical boutique precision for fine academic tabulation columns, grading scales, and marks.',
      badge: 'High Precision',
      color: 'indigo',
    },
    {
      name: 'ChatGPT',
      model: 'GPT-4o Vision',
      url: 'https://chatgpt.com',
      description: 'Fast optical character recognition and multi-table extraction.',
      badge: 'Fast',
      color: 'emerald',
    },
  ]);

  const [isCopied, setIsCopied] = useState<boolean>(false);
  const [markdownInput, setMarkdownInput] = useState<string>('');
  const [dragOver, setDragOver] = useState<boolean>(false);
  const [selectedFileName, setSelectedFileName] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Fetch universal prompt and AI links from API
    api.getClaudePrompt()
      .then((res: any) => {
        if (res?.prompt) setPromptText(res.prompt);
        if (res?.ai_tools && Array.isArray(res.ai_tools)) setAiTools(res.ai_tools);
      })
      .catch(() => {
        // Fallback universal prompt
        setPromptText(
          "You are an expert academic tabulation and document extraction assistant.\n" +
          "You are provided with one or more scanned/photographed academic result sheet image(s) from a university or college.\n\n" +
          "Please perform comprehensive tabular data extraction across ALL provided pages and merge them into a single, complete Markdown document.\n\n" +
          "### Extraction Instructions:\n" +
          "1. Header Metadata: Extract University/Institution Name, Faculty, Department, Degree/Program, Semester/Year, Session/Batch, and Total Semester Credits.\n" +
          "2. Course Detection: Extract ALL courses present on the sheet, noting Course Code, Course Title, and Credit Hours in the bulleted Course List (e.g. `- [CSE-1101]: Structured Programming (Credit: 3.00)`).\n" +
          "3. Multi-Page Merging: If multiple photos/pages are uploaded, extract EVERY single student across Page 1, Page 2, Page 3, etc., and merge all rows sequentially sorted by Serial Number (S/N) or Student ID into ONE continuous table.\n" +
          "4. Semester 1.1 / 1st Semester Rule: For 1st Year 1st Semester (Semester 1.1 / first exam), the Current Semester GPA is identical to the Cumulative CGPA (CGPA = GPA) because it is the only examination that has taken place. Always populate both GPA and CGPA columns (if the sheet only prints GPA, duplicate that GPA value into the CGPA column, and Total Semester Credits into the Cumulative Credits column).\n" +
          "5. Strict Row Alignment & ID Cross-Verification: You MUST double-check each Student ID against that specific person's exact Name, Serial Number, and course marks from the image. Ensure the Student ID, Student Name, Course Grades, and GPA strictly correspond to the same horizontal row from the sheet — NEVER shift, swap, transpose, or misalign any student's ID or results with neighboring rows.\n\n" +
          "### Strict Output Constraints:\n" +
          "- CRITICAL: Output ONLY the clean Markdown document starting directly with `# Academic Result Sheet`.\n" +
          "- Do NOT write any conversational intro, greetings, explanations, or trailing commentary.\n" +
          "- Student ID & Name Fidelity: Double-check that every Student ID is 100% matched with the correct student name and row on the sheet. Keep complete original Student ID format without truncation.\n" +
          "- Grade Points (GP): Normalize to 2 decimal places (e.g. 4.00, 3.75, 3.50, 3.25, 3.00, 2.75, 2.50, 2.25, 2.00, 0.00).\n" +
          "- Letter Grades (LG): Exact letter grades (A+, A, A-, B+, B, B-, C+, C, D, F).\n" +
          "- Output pure raw Markdown table only.\n\n" +
          "Output strictly in clean Markdown format with the exact structure below:\n\n" +
          "# Academic Result Sheet\n" +
          "- **Institution**: [Extracted Institution Name]\n" +
          "- **Department**: [Extracted Department Name]\n" +
          "- **Semester**: [Extracted Semester / Exam Name]\n" +
          "- **Session / Batch**: [Extracted Session / Batch]\n" +
          "- **Total Semester Credit**: [e.g. 21.50]\n\n" +
          "### Course List:\n" +
          "- [Course Code 1]: [Course Title 1] (Credit: [X.XX])\n" +
          "- [Course Code 2]: [Course Title 2] (Credit: [X.XX])\n" +
          "...\n\n" +
          "| S/N | Student ID | Student Name | [CODE_1] GP | [CODE_1] LG | [CODE_2] GP | [CODE_2] LG | ... | Total GP | GPA | Cumulative Credits | CGPA | Result Status |\n" +
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|\n" +
          "| 1 | [ID 1] | [Name 1] | 4.00 | A+ | 3.75 | A | ... | 78.50 | 3.85 | 21.50 | 3.85 | P |\n"
        );
      });
  }, []);

  const handleCopyPrompt = async () => {
    try {
      await navigator.clipboard.writeText(promptText);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2500);
    } catch (err) {
      console.error('Failed to copy prompt', err);
    }
  };

  const handleFileUpload = (file: File) => {
    setErrorMsg(null);
    if (!file.name.endsWith('.md') && !file.name.endsWith('.txt') && !file.name.endsWith('.markdown')) {
      setErrorMsg('Please upload a valid .md or .txt Markdown file.');
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      if (text) {
        setMarkdownInput(text);
        setSelectedFileName(file.name);
      }
    };
    reader.readAsText(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!markdownInput.trim()) {
      setErrorMsg('Please paste or upload Markdown content from your vision AI first.');
      return;
    }
    setErrorMsg(null);
    try {
      await onMarkdownSubmit(markdownInput, selectedFileName || 'ai_extracted.md');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to process Markdown dataset.');
    }
  };

  // Real-time Markdown dynamic metadata inspector
  const detectedDept = (markdownInput.match(/[-*]\s*\*\*Department\*\*:\s*([^\n\r]+)/i) || [])[1]?.trim();
  const detectedSemester = (markdownInput.match(/[-*]\s*\*\*Semester\*\*:\s*([^\n\r]+)/i) || [])[1]?.trim();
  const detectedInst = (markdownInput.match(/[-*]\s*\*\*Institution\*\*:\s*([^\n\r]+)/i) || [])[1]?.trim();
  const estimatedStudents = (markdownInput.match(/\|\s*[A-Z0-9]{4,14}\s*\|/g) || []).length;
  const detectedCourses = (markdownInput.match(/\|\s*[A-Z]{2,6}[-_]?[0-9]{3,4}[A-Z]?\s*(?:GP|\(GP\)|LG)?/gi) || []).length / 2;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-emerald-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-start sm:items-center gap-3.5 min-w-0 flex-1">
          <div className="w-11 h-11 sm:w-12 sm:h-12 rounded-xl bg-emerald-500/10 dark:bg-emerald-500/15 border border-emerald-500/20 dark:border-emerald-500/30 flex items-center justify-center flex-shrink-0 text-emerald-600 dark:text-emerald-400 mt-0.5 sm:mt-0">
            <Sparkles className="w-5 h-5 sm:w-6 sm:h-6" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Extract Result Sheet with Vision AI
              </h3>
              <Badge variant="emerald" size="sm">
                Universal: Any Department &amp; Semester
              </Badge>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Copy the prompt, open any of the links below (<span className="text-amber-600 dark:text-amber-300 font-semibold">Google AI Studio</span>, <span className="text-sky-600 dark:text-sky-300 font-semibold">Claude</span>, or <span className="text-emerald-600 dark:text-emerald-300 font-semibold">ChatGPT</span>), attach clean, well-lit &amp; neatly cropped photos of your result sheets (with all student rows, course columns &amp; header visible), and paste the generated Markdown table below.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 w-full md:w-auto">
          <Button
            variant="primary"
            size="sm"
            onClick={handleCopyPrompt}
            leftIcon={isCopied ? <Check className="w-4 h-4 text-white" /> : <Copy className="w-4 h-4" />}
            className="flex-1 md:flex-none text-xs font-bold px-4 py-2"
          >
            {isCopied ? '✓ Prompt Copied to Clipboard!' : 'Copy Extraction Prompt'}
          </Button>
        </div>
      </div>

      {/* AI Vision Studios Link Hub */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 px-1">
          <span className="font-semibold text-slate-800 dark:text-slate-300 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-sky-500 dark:text-sky-400" />
            Recommended Vision AI Studios (Free & Instant):
          </span>
          <span>Click any studio to open in new tab</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
          {aiTools.map((tool, idx) => (
            <a
              key={idx}
              href={tool.url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 rounded-2xl bg-white dark:bg-slate-900/70 hover:bg-slate-50 dark:hover:bg-slate-800/80 border border-slate-200 dark:border-slate-800 hover:border-emerald-500/50 dark:hover:border-emerald-500/50 transition-all group flex flex-col justify-between space-y-3 shadow-sm hover:scale-[1.01] active:scale-[0.99]"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                      {tool.name}
                    </span>
                    <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-emerald-500 transition-colors" />
                  </div>
                  <Badge variant={tool.name.includes('Google') ? 'amber' : tool.name.includes('Claude') ? 'blue' : 'emerald'} size="sm">
                    {tool.badge}
                  </Badge>
                </div>
                <div className="text-[11px] font-mono text-sky-600 dark:text-sky-400 font-medium">
                  {tool.model}
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  {tool.description}
                </p>
              </div>

              <div className="pt-2 border-t border-slate-100 dark:border-slate-800/60 flex items-center justify-between text-[11px] text-slate-700 dark:text-slate-300 font-semibold group-hover:text-emerald-600 dark:group-hover:text-white">
                <span>Launch {tool.name}</span>
                <span className="text-emerald-500 group-hover:translate-x-1 transition-transform">→</span>
              </div>
            </a>
          ))}
        </div>
      </div>

      {/* 3-Step Guided Workflow */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        <Card className="p-4 flex flex-col justify-between space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-sky-600 dark:text-sky-400 font-mono">STEP 1</span>
            <Badge variant="blue" size="sm">Copy</Badge>
          </div>
          <p className="text-xs font-semibold text-slate-900 dark:text-slate-200">1. Copy Extraction Prompt</p>
          <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
            Click "Copy Extraction Prompt" above. It instructs the AI to recognize course codes, credit hours, grades, and merge multi-page tables into one.
          </p>
        </Card>

        <Card className="p-4 flex flex-col justify-between space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-amber-600 dark:text-amber-400 font-mono">STEP 2</span>
            <Badge variant="amber" size="sm">Clean & Cropped</Badge>
          </div>
          <p className="text-xs font-semibold text-slate-900 dark:text-slate-200">2. Take Clean, Cropped Photos</p>
          <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
            Ensure good lighting, zero glare, and flat orientation. Crop to include all table borders, columns (IDs, Course GPs/LGs, GPA/CGPA), and department header. Upload Page 1, Page 2, etc. together into AI.
          </p>
        </Card>

        <Card className="p-4 flex flex-col justify-between space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 font-mono">STEP 3</span>
            <Badge variant="emerald" size="sm">Instant Ingestion</Badge>
          </div>
          <p className="text-xs font-semibold text-slate-900 dark:text-slate-200">3. Paste or Upload .md</p>
          <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
            Copy the AI's Markdown table output and paste it below (or upload the .md file). The engine will parse all records and unlock the dashboard.
          </p>
        </Card>
      </div>

      {/* Navigation Tabs (Directly above the upload/paste box) */}
      {navigationTabs && (
        <div className="pt-2">
          {navigationTabs}
        </div>
      )}

      {/* Input Area: Dropzone + Textarea */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <label className="text-xs font-bold text-slate-800 dark:text-slate-300 flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
            Paste AI Markdown Table or Drop .md File:
          </label>

          {/* Dynamic Detection Badges */}
          <div className="flex flex-wrap items-center gap-1.5">
            {detectedInst && (
              <span className="text-[10px] font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800/80 px-2 py-0.5 rounded-md flex items-center gap-1 border border-slate-200 dark:border-slate-700">
                <Building2 className="w-3 h-3 text-slate-500 dark:text-slate-400" />
                {detectedInst}
              </span>
            )}
            {detectedDept && (
              <span className="text-[10px] font-medium text-sky-800 dark:text-sky-300 bg-sky-50 dark:bg-sky-950/60 px-2 py-0.5 rounded-md flex items-center gap-1 border border-sky-200 dark:border-sky-800/60">
                <GraduationCap className="w-3 h-3 text-sky-500 dark:text-sky-400" />
                {detectedDept}
              </span>
            )}
            {detectedSemester && (
              <span className="text-[10px] font-medium text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded-md flex items-center gap-1 border border-emerald-200 dark:border-emerald-800/60">
                <BookOpen className="w-3 h-3 text-emerald-500 dark:text-emerald-400" />
                {detectedSemester}
              </span>
            )}
            {detectedCourses > 0 && (
              <span className="text-[10px] font-medium text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/60 px-2 py-0.5 rounded-md flex items-center gap-1 border border-amber-200 dark:border-amber-800/60">
                <BookOpen className="w-3 h-3 text-amber-500 dark:text-amber-400" />
                {Math.round(detectedCourses)} Courses
              </span>
            )}
            {estimatedStudents > 0 && (
              <span className="text-xs font-mono font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/80 px-2.5 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800">
                ✓ ~{estimatedStudents} Students Detected
              </span>
            )}
          </div>
        </div>

        {/* Drag & Drop Box */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-2xl transition-all ${dragOver
              ? 'border-emerald-500 bg-emerald-500/5 shadow-lg shadow-emerald-500/10'
              : 'border-slate-300 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 hover:border-slate-400 dark:hover:border-slate-700'
            }`}
        >
          <textarea
            value={markdownInput}
            onChange={(e) => setMarkdownInput(e.target.value)}
            placeholder="# Academic Result Sheet&#10;- **Institution**: Jagannath University&#10;- **Department**: Department of Computer Science & Engineering&#10;- **Semester**: BSc 1st Year 2nd Semester Examination 2023&#10;- **Session / Batch**: Session: 2022-23&#10;&#10;| S/N | Student ID | Student Name | CSE-1201 GP | CSE-1201 LG | CSEL-1202 GP | CSEL-1202 LG | ... | GPA | CGPA |&#10;| 1 | B220305009 | MD. TANVIR HASAN | 4.00 | A+ | 3.75 | A | ... | 3.88 | 3.82 |"
            rows={9}
            className="w-full p-4 bg-transparent text-slate-900 dark:text-slate-100 text-xs font-mono resize-y focus:outline-none placeholder-slate-400 dark:placeholder-slate-600"
          />

          {/* Quick Upload Action Bar */}
          <div className="p-3 border-t border-slate-200 dark:border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-3 bg-white dark:bg-slate-950/40 rounded-b-2xl">
            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <input
                type="file"
                ref={fileInputRef}
                accept=".md,.markdown,.txt"
                onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="inline-flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 hover:text-emerald-500 font-medium transition-colors"
              >
                <UploadCloud className="w-3.5 h-3.5" />
                Upload .md file instead
              </button>
              {selectedFileName && (
                <span className="text-slate-800 dark:text-slate-300 font-mono text-[11px] bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-transparent">
                  {selectedFileName}
                </span>
              )}
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              {markdownInput && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => { setMarkdownInput(''); setSelectedFileName(''); setErrorMsg(null); }}
                  className="text-xs text-slate-400 hover:text-rose-400"
                >
                  Clear
                </Button>
              )}
              <Button
                size="md"
                onClick={handleSubmit}
                disabled={!markdownInput.trim() || isProcessing}
                leftIcon={isProcessing ? <Loader2 className="w-4 h-4 animate-spin text-emerald-300" /> : <Sparkles className="w-4 h-4 text-emerald-300" />}
                className="w-full sm:w-auto bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold shadow-lg shadow-emerald-900/30"
              >
                {isProcessing ? 'Analyzing Dataset...' : 'Analyze the Dataset →'}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 flex items-center justify-between text-rose-200 text-xs shadow-lg">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-rose-400 hover:text-rose-200 p-1">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
