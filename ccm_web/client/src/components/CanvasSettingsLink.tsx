import type { JSX } from 'react'
import { Link } from '@mui/material'

interface CanvasSettingsLinkProps {
  url: string
  msg?: string
}

export default function CanvasSettingsLink (props: CanvasSettingsLinkProps): JSX.Element {
  const url = props.url
  const msg = props.msg ?? 'Canvas Settings page'
  return <Link href={url} target='_parent'>{msg}</Link>
}
