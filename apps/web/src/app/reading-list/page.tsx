import { BookOpen } from "lucide-react";

const columns = ["To Read", "In Progress", "Done"];

export default function ReadingListPage() {
  return (
    <div className="p-6 h-screen flex flex-col">
      <header className="border-b border-[var(--sidebar-border)] pb-4 mb-6">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <BookOpen size={20} className="text-[var(--accent)]" />
          Reading List
        </h2>
        <p className="text-xs text-[var(--muted)] mt-1">
          Organize papers and articles in a kanban board
        </p>
      </header>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4 min-h-0">
        {columns.map((col) => (
          <div
            key={col}
            className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-4 flex flex-col"
          >
            <h3 className="text-sm font-medium mb-3 pb-2 border-b border-[var(--card-border)]">
              {col}
            </h3>
            <div className="flex-1 flex items-center justify-center">
              <p className="text-xs text-[var(--muted)]">
                Drop items here
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
