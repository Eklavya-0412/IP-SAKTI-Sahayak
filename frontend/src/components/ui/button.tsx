import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib'
const buttonVariants=cva('inline-flex items-center justify-center gap-2 rounded-lg border border-transparent px-4 py-2.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400',{variants:{variant:{default:'bg-emerald-500 text-slate-950 hover:bg-emerald-400',outline:'border-slate-700 bg-slate-900/60 text-slate-200 hover:bg-slate-800',ghost:'text-slate-300 hover:bg-slate-800',secondary:'bg-teal-950 text-teal-300 hover:bg-teal-900',destructive:'bg-red-800 text-white hover:bg-red-700'},size:{default:'',sm:'px-3 py-1.5 text-xs',icon:'size-9 p-2'}},defaultVariants:{variant:'default',size:'default'}})
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>,VariantProps<typeof buttonVariants>{asChild?:boolean}
export const Button=React.forwardRef<HTMLButtonElement,ButtonProps>(({className,variant,size,asChild=false,...props},ref)=>{const Comp=asChild?Slot:'button';return <Comp className={cn(buttonVariants({variant,size,className}))} ref={ref} {...props}/>})
Button.displayName='Button'
