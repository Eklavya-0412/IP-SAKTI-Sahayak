import * as React from 'react'
import * as DialogPrimitive from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { cn } from '../../lib'
export const Dialog=DialogPrimitive.Root
export const DialogTrigger=DialogPrimitive.Trigger
export const DialogTitle=DialogPrimitive.Title
export const DialogDescription=DialogPrimitive.Description
export const DialogClose=DialogPrimitive.Close
export const DialogContent=React.forwardRef<React.ElementRef<typeof DialogPrimitive.Content>,React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>&{sheet?:boolean}>(({className,children,sheet=false,...props},ref)=><DialogPrimitive.Portal><DialogPrimitive.Overlay className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm"/><DialogPrimitive.Content ref={ref} className={cn(sheet?'fixed inset-y-0 right-0 z-50 w-full max-w-xl overflow-y-auto border-l border-slate-800 bg-slate-950 p-6 text-slate-100 shadow-2xl sm:p-8':'fixed left-1/2 top-1/2 z-50 max-h-[90vh] w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-2xl border border-slate-800 bg-slate-950 p-6 text-slate-100 shadow-2xl','[&_button]:cursor-pointer [&_button:disabled]:cursor-not-allowed [&_button:disabled]:opacity-50 [&_input]:max-w-full [&_input]:rounded-lg [&_input]:border [&_input]:border-slate-700 [&_input]:bg-slate-900 [&_input]:p-3 [&_input]:text-slate-100 [&_input[type=checkbox]]:accent-emerald-500 [&_select]:max-w-full [&_select]:rounded-lg [&_select]:border [&_select]:border-slate-700 [&_select]:bg-slate-900 [&_select]:p-2 [&_textarea]:rounded-lg [&_textarea]:border [&_textarea]:border-slate-700 [&_textarea]:bg-slate-900 [&_textarea]:p-3 [&_p]:leading-relaxed [&_:focus-visible]:outline-2 [&_:focus-visible]:outline-offset-2 [&_:focus-visible]:outline-emerald-400',className)} {...props}>{children}<DialogPrimitive.Close className="absolute right-3 top-3 rounded-lg p-2 text-slate-400 hover:bg-slate-800" aria-label="Close"><X size={20}/></DialogPrimitive.Close></DialogPrimitive.Content></DialogPrimitive.Portal>)
DialogContent.displayName='DialogContent'
