import * as React from 'react'
import * as DialogPrimitive from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { cn } from '../../lib'
export const Dialog=DialogPrimitive.Root
export const DialogTrigger=DialogPrimitive.Trigger
export const DialogTitle=DialogPrimitive.Title
export const DialogDescription=DialogPrimitive.Description
export const DialogClose=DialogPrimitive.Close
export const DialogContent=React.forwardRef<React.ElementRef<typeof DialogPrimitive.Content>,React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>&{sheet?:boolean}>(({className,children,sheet=false,...props},ref)=><DialogPrimitive.Portal><DialogPrimitive.Overlay className="dialog-overlay"/><DialogPrimitive.Content ref={ref} className={cn(sheet?'sheet':'dialog',className)} {...props}>{children}<DialogPrimitive.Close className="dialog-close" aria-label="Close"><X size={20}/></DialogPrimitive.Close></DialogPrimitive.Content></DialogPrimitive.Portal>)
DialogContent.displayName='DialogContent'
