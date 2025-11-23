import { DocumentFileData } from "../index";

export function ChatFiles({ data }: { data: DocumentFileData }) {
  if (!data.files.length) return null;
  return (
    <div className="flex gap-2 items-center">
      {data.files.map((file) => (
        <div key={file.id} className="text-sm text-muted-foreground">
          {file.filename}
        </div>
      ))}
    </div>
  );
}
