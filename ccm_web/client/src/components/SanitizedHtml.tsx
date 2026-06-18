import React from 'react'
import DOMPurify from 'dompurify'

interface SanitizedHtmlProps {
  html: string
  className?: string
}

/*
  Renders admin-authored HTML (e.g. the configurable banner and footer flatpages)
  after sanitizing it with DOMPurify. This is the single trusted boundary for
  rendering HTML that did not originate in the client bundle. Renders nothing when
  the content is empty or whitespace.
*/
function SanitizedHtml (props: SanitizedHtmlProps): JSX.Element | null {
  const { html, className } = props
  if (html.trim() === '') return null
  return (
    <div className={className} dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />
  )
}

export default SanitizedHtml
