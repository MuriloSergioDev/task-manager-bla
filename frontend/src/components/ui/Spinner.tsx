import { LoaderCircle } from 'lucide-react'

export function Spinner({ className = '' }: { className?: string }) {
  return <LoaderCircle className={`animate-spin motion-reduce:animate-none ${className}`} role="status" aria-label="Loading" />
}
