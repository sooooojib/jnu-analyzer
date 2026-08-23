import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Copy,
  Check,
  ExternalLink,
  UploadCloud,
  X,
  Loader2,
  GraduationCap,
  BookOpen,
  Building2,
  Sun,
  Crop,
  Eye,
  Terminal,
  Star,
  ArrowRight,
} from 'lucide-react';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
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
      model: 'Gemini 3.1 Pro / Pro (Latest)',
      url: 'https://aistudio.google.com',
      description: 'Recommended for Multi-Page Merging: Upload 2–10+ photos at once with massive 2M token context window.',
      badge: '#1 Recommended',
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

  // Fetch universal prompt template from backend
  useEffect(() => {
    api.getClaudePrompt()
      .then((res: any) => {
        if (res?.prompt) setPromptText(res.prompt);
        if (res?.ai_tools && Array.isArray(res.ai_tools)) setAiTools(res.ai_tools);
      })
      .catch(() => {
        // Fallback universal prompt
        setPromptText(
          "You are a world-class academic data extraction and precision OCR engine.\n" +
          "You are provided with one or more scanned/photographed academic tabulation result sheets from a university.\n\n" +
          "Your goal is to extract 100% of the records into a single, flawless Markdown document.\n\n" +
          "### Extraction Instructions:\n" +
          "1. Header Metadata: Extract Institution Name, Department, Semester/Year, Session/Batch, and Total Semester Credit.\n" +
          "2. Course Detection: Extract all courses present, noting Course Code, Course Title, and Credit Hours in a bulleted list.\n" +
          "3. Multi-Page Merging: If multiple images are provided of the *same exam*, merge all student rows sequentially by Serial Number (S/N) into ONE continuous table. Do NOT skip any rows. (Note: If images represent different semesters with different courses, generate separate tables).\n" +
          "4. Strict Row Alignment: Trace each horizontal row strictly. You MUST double-check each Student ID against that specific person's Name and course marks. NEVER shift, swap, or misalign data with neighboring rows.\n" +
          "5. Column Mapping Rules:\n" +
          "   - Map the sheet's \"Total Grade Point (TGP)\" (for the current semester) to your output column `Total GP`.\n" +
          "   - Map the sheet's \"GPA\" or \"Total Grade Point Ave.\" to `GPA`.\n" +
          "   - Map the sheet's \"Total Credit Point (TCP)\" under Cumulative Results to `Cumulative Credits`.\n" +
          "   - Map the sheet's \"Comments\" (e.g., P, CP, NP) to `Result Status`.\n" +
          "6. Missing Data: If a student is completely missing a grade for a course (e.g., absent), output `-` for both GP and LG.\n\n" +
          "### Official Grading Scale & Verification Rules:\n" +
          "- A+ = 4.00 | A = 3.75 | A- = 3.50 | B+ = 3.25 | B = 3.00 | B- = 2.75 | C+ = 2.50 | C = 2.25 | D = 2.00 | F = 0.00\n" +
          "- 1st Semester Rule: If this is 1st Year 1st Semester, GPA always equals CGPA. Populate both columns.\n" +
          "- Normalize all Grade Points to 2 decimal places (e.g., 4.00, 3.50, 0.00).\n\n" +
          "### Output Structure & Constraints:\n" +
          "You must first use an `<analysis_scratchpad>` block to silently verify ambiguous characters, check math for hard-to-read rows, and map the column headers.\n" +
          "Immediately following the scratchpad, output the exact Markdown format. Do NOT output any conversational text outside of these blocks.\n\n" +
          "Use this exact output template:\n\n" +
          "<analysis_scratchpad>\n" +
          "- Course columns detected: [list courses]\n" +
          "- Checking ambiguous row S/N X... [brief math check if needed]\n" +
          "</analysis_scratchpad>\n\n" +
          "# Academic Result Sheet\n" +
          "- **Institution**: [Name]\n" +
          "- **Department**: [Name]\n" +
          "- **Semester**: [Name]\n" +
          "- **Session / Batch**: [Name]\n" +
          "- **Total Semester Credit**: [X.XX]\n\n" +
          "### Course List:\n" +
          "- [Course Code]: [Course Title] (Credit: [X.XX])\n\n" +
          "| S/N | Student ID | Student Name | [CODE_1] GP | [CODE_1] LG | [CODE_2] GP | [CODE_2] LG | ... | Total GP | GPA | Cumulative Credits | CGPA | Result Status |\n" +
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|\n" +
          "| 1 | [ID] | [Name] | 4.00 | A+ | 3.75 | A | ... | 78.50 | 3.85 | 21.50 | 3.85 | P |\n"
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
    <div className="space-y-8">
      {/* STEP 1: Copy Extraction Prompt */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 py-1">
        <div className="space-y-1 max-w-2xl">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono font-bold text-emerald-600 dark:text-emerald-400">
              STEP 1
            </span>
            <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100">
              Copy Extraction Prompt
            </h3>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
            Copy the universal prompt. It instructs AI models to read all student IDs, names, course GPs/LGs, and merge multi-page tabulation sheets into a single Markdown table.
          </p>
        </div>

        {/* Dark Snippet Container */}
        <div className="bg-slate-900/90 dark:bg-black/40 border border-slate-700/60 dark:border-white/10 p-2 rounded-xl flex items-center justify-between sm:justify-start gap-3 shadow-inner shrink-0">
          <div className="flex items-center gap-2 pl-2 pr-1 text-xs font-mono text-slate-400">
            <Terminal className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>prompt.txt</span>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={handleCopyPrompt}
            leftIcon={isCopied ? <Check className="w-4 h-4 text-white" /> : <Copy className="w-4 h-4" />}
            className="text-xs font-bold px-4 py-2 hover:opacity-90 active:scale-[0.98] transition-all shrink-0"
          >
            {isCopied ? 'Prompt Copied!' : 'Copy Extraction Prompt'}
          </Button>
        </div>
      </div>

      {/* STEP 2: Select Vision AI Studio */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono font-bold text-sky-600 dark:text-sky-400">
              STEP 2
            </span>
            <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100">
              Choose Vision AI Studio
            </h3>
          </div>
        </div>

        {/* 3-Step Human-Friendly Photo Prep Guide */}
        <div className="bg-slate-100/80 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800/60 rounded-xl p-5">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
            {/* Step A */}
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-amber-500/10 dark:bg-amber-500/15 flex items-center justify-center shrink-0">
                  <Sun className="w-4 h-4 text-amber-500" />
                </div>
                <h4 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-slate-200">
                  1. Good Lighting
                </h4>
              </div>
              <p className="text-slate-500 dark:text-slate-400 text-xs sm:text-sm leading-relaxed">
                Take a clear photo in a bright room. Avoid using a flash if it creates a white glare on the paper or screen.
              </p>
            </div>

            {/* Step B */}
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-sky-500/10 dark:bg-sky-500/15 flex items-center justify-center shrink-0">
                  <Crop className="w-4 h-4 text-sky-500" />
                </div>
                <h4 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-slate-200">
                  2. Tight Cropping
                </h4>
              </div>
              <p className="text-slate-500 dark:text-slate-400 text-xs sm:text-sm leading-relaxed">
                Before uploading to the AI, crop the photo. Cut out the desk, background, or empty margins so only the data table is visible.
              </p>
            </div>

            {/* Step C */}
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-emerald-500/10 dark:bg-emerald-500/15 flex items-center justify-center shrink-0">
                  <Eye className="w-4 h-4 text-emerald-500" />
                </div>
                <h4 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-slate-200">
                  3. Clear Legibility
                </h4>
              </div>
              <p className="text-slate-500 dark:text-slate-400 text-xs sm:text-sm leading-relaxed">
                Zoom in on your photo. Can you easily read every student ID and grade? If it's blurry for you, the AI will struggle too.
              </p>
            </div>
          </div>
        </div>

        {/* 3 AI Studio Cards (Responsive: Stack on Mobile, 3-Cols on Desktop) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 md:gap-4">
          {aiTools.map((tool, idx) => {
            const isGoogle = tool.name.toLowerCase().includes('google');
            return (
              <a
                key={idx}
                href={tool.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`p-3.5 sm:p-4 rounded-xl transition-all group flex flex-col justify-between space-y-2.5 ${
                  isGoogle
                    ? 'bg-amber-500/10 dark:bg-amber-500/15 border border-amber-500/30 hover:border-amber-500/60 shadow-sm hover:scale-[1.01] active:scale-[0.99]'
                    : 'bg-white dark:bg-slate-900/60 hover:bg-slate-50 dark:hover:bg-slate-800/80 border border-slate-200 dark:border-slate-800/80 hover:border-emerald-500/40 dark:hover:border-emerald-500/40 shadow-sm hover:scale-[1.01] active:scale-[0.99]'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className={`text-xs sm:text-sm font-bold ${isGoogle ? 'text-amber-950 dark:text-amber-300' : 'text-slate-900 dark:text-slate-100 group-hover:text-emerald-600 dark:group-hover:text-emerald-400'}`}>
                      {tool.name}
                    </span>
                    <Badge variant={isGoogle ? 'amber' : tool.name.includes('Claude') ? 'blue' : 'emerald'} size="sm" className="inline-flex items-center gap-1">
                      {isGoogle && <Star className="w-3 h-3 fill-amber-500 text-amber-500 shrink-0" />}
                      <span>{tool.badge}</span>
                    </Badge>
                  </div>

                  <div className={`text-[11px] font-mono font-medium ${isGoogle ? 'text-amber-600 dark:text-amber-400' : 'text-sky-600 dark:text-sky-400'}`}>
                    {tool.model}
                  </div>

                  <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed line-clamp-2">
                    {tool.description}
                  </p>
                </div>

                <div className={`pt-2 border-t ${isGoogle ? 'border-amber-500/20 text-amber-900 dark:text-amber-300' : 'border-slate-100 dark:border-slate-800/60 text-slate-600 dark:text-slate-400'} flex items-center justify-between text-[11px] font-medium`}>
                  <span>Open studio</span>
                  <ExternalLink className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </a>
            );
          })}
        </div>
      </div>

      {/* Navigation Tabs (if injected) */}
      {navigationTabs && (
        <div>
          {navigationTabs}
        </div>
      )}

      {/* STEP 3: Paste Markdown Output */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono font-bold text-emerald-600 dark:text-emerald-400">
              STEP 3
            </span>
            <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100">
              Paste Extracted Markdown
            </h3>
          </div>

          {/* Dynamic Detection Badges */}
          <div className="flex flex-wrap items-center gap-1.5">
            {detectedInst && (
              <span className="text-[10px] font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800/80 px-2 py-0.5 rounded-md flex items-center gap-1">
                <Building2 className="w-3 h-3 text-slate-500 dark:text-slate-400" />
                {detectedInst}
              </span>
            )}
            {detectedDept && (
              <span className="text-[10px] font-medium text-sky-800 dark:text-sky-300 bg-sky-50 dark:bg-sky-950/60 px-2 py-0.5 rounded-md flex items-center gap-1">
                <GraduationCap className="w-3 h-3 text-sky-500 dark:text-sky-400" />
                {detectedDept}
              </span>
            )}
            {detectedSemester && (
              <span className="text-[10px] font-medium text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded-md flex items-center gap-1">
                <BookOpen className="w-3 h-3 text-emerald-500 dark:text-emerald-400" />
                {detectedSemester}
              </span>
            )}
            {detectedCourses > 0 && (
              <span className="text-[10px] font-medium text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/60 px-2 py-0.5 rounded-md flex items-center gap-1">
                <BookOpen className="w-3 h-3 text-amber-500 dark:text-amber-400" />
                {Math.round(detectedCourses)} Courses
              </span>
            )}
            {estimatedStudents > 0 && (
              <span className="text-xs font-mono font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/80 px-2.5 py-0.5 rounded-full inline-flex items-center gap-1.5">
                <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                <span>~{estimatedStudents} Students Detected</span>
              </span>
            )}
          </div>
        </div>

        {/* Sleek Code Editor Block */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={`rounded-2xl transition-all overflow-hidden bg-slate-50 dark:bg-slate-900/60 ${
            dragOver ? 'ring-2 ring-emerald-500 bg-emerald-500/5' : ''
          }`}
        >
          <textarea
            value={markdownInput}
            onChange={(e) => setMarkdownInput(e.target.value)}
            placeholder="# Academic Result Sheet&#10;- **Institution**: Jagannath University&#10;- **Department**: Department of Computer Science & Engineering&#10;- **Semester**: BSc 1st Year 1st Semester Examination 2023&#10;- **Session / Batch**: Session: 2022-23&#10;&#10;| S/N | Student ID | Student Name | CSE-1101 GP | CSE-1101 LG | ... | Total GP | GPA | Cumulative Credits | CGPA | Result Status |&#10;| 1 | B210305018 | FEERDAUS HASAN PRINCE | 2.50 | C+ | ... | 33.00 | 1.61 | 20.50 | 1.61 | CP |"
            rows={10}
            className="w-full p-4 sm:p-5 bg-transparent text-slate-900 dark:text-slate-100 text-xs font-mono resize-y focus:outline-none placeholder-slate-400 dark:placeholder-slate-600 leading-relaxed"
          />

          {/* Bottom Bar within Editor */}
          <div className="px-4 py-2.5 bg-slate-100/70 dark:bg-slate-950/50 flex flex-col sm:flex-row items-center justify-between gap-2.5">
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
                <span className="text-slate-800 dark:text-slate-300 font-mono text-[11px] bg-white dark:bg-slate-800 px-2 py-0.5 rounded">
                  {selectedFileName}
                </span>
              )}
            </div>

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

      {/* Primary Centered Call-To-Action Button */}
      <div className="flex justify-center pt-2 pb-4">
        <Button
          size="lg"
          onClick={handleSubmit}
          disabled={!markdownInput.trim() || isProcessing}
          leftIcon={isProcessing ? <Loader2 className="w-5 h-5 animate-spin text-emerald-300" /> : <Sparkles className="w-5 h-5 text-emerald-300" />}
          rightIcon={!isProcessing ? <ArrowRight className="w-4 h-4 text-emerald-200" /> : undefined}
          className="px-8 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-sm font-bold shadow-lg shadow-emerald-900/30 w-full sm:w-auto"
        >
          {isProcessing ? 'Analyzing Dataset...' : 'Analyze the Dataset'}
        </Button>
      </div>
    </div>
  );
};
