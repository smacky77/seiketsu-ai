import { cn } from "@/lib/utils/cn"

export function TestCSS() {
  return (
    <div className="p-4 space-y-4">
      <h2 className="text-2xl font-bold">CSS Configuration Test</h2>
      
      {/* Test shadcn/ui classes */}
      <div className="space-y-2">
        <div className={cn("p-4", "bg-background", "text-foreground", "border", "border-border", "rounded-md")}>
          Background & Border Test
        </div>
        
        <div className={cn("p-4", "bg-card", "text-card-foreground", "border", "border-border", "rounded-md", "shadow-sm")}>
          Card Background Test
        </div>
        
        <div className={cn("p-4", "bg-primary", "text-primary-foreground", "rounded-md")}>
          Primary Colors Test
        </div>
        
        <div className={cn("p-4", "bg-secondary", "text-secondary-foreground", "rounded-md")}>
          Secondary Colors Test
        </div>
        
        <div className={cn("p-4", "bg-muted", "text-muted-foreground", "rounded-md")}>
          Muted Colors Test
        </div>
        
        <div className={cn("p-4", "bg-accent", "text-accent-foreground", "rounded-md")}>
          Accent Colors Test
        </div>
        
        <input 
          className={cn("w-full", "p-2", "border", "border-input", "bg-background", "text-foreground", "rounded-md", "focus:ring-2", "focus:ring-ring")}
          placeholder="Input styling test"
        />
      </div>
    </div>
  )
}