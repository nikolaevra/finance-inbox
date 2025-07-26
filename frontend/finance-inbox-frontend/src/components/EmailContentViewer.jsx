import React, { useRef, useEffect } from 'react'

const EmailContentViewer = ({ htmlContent, textContent, activeTab = 'html' }) => {
  const iframeRef = useRef(null)

  useEffect(() => {
    if (activeTab === 'html' && htmlContent && iframeRef.current) {
      const iframe = iframeRef.current
      const iframeDoc = iframe.contentDocument || iframe.contentWindow.document
      
      // Create isolated HTML content with reset styles
      const isolatedHTML = `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            /* Reset styles to prevent inheritance from parent */
            * {
              box-sizing: border-box;
            }
            
            body {
              margin: 0;
              padding: 16px;
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              line-height: 1.6;
              color: #374151;
              background: transparent;
              word-wrap: break-word;
              overflow-wrap: break-word;
            }
            
            /* Email content container */
            .email-content {
              max-width: none;
              overflow-wrap: break-word;
              word-break: break-word;
            }
            
            /* Reset common email styles that might conflict */
            .email-content h1, .email-content h2, .email-content h3, 
            .email-content h4, .email-content h5, .email-content h6 {
              margin: 0.5em 0;
              font-weight: 600;
            }
            
            .email-content p {
              margin: 0.5em 0;
            }
            
            .email-content a {
              color: #3b82f6;
              text-decoration: underline;
            }
            
            .email-content a:hover {
              color: #2563eb;
            }
            
            .email-content img {
              max-width: 100%;
              height: auto;
            }
            
            .email-content table {
              border-collapse: collapse;
              width: 100%;
            }
            
            .email-content td, .email-content th {
              padding: 8px;
              text-align: left;
              border: 1px solid #e5e7eb;
            }
            
            /* Prevent any styles from affecting parent document */
            .email-content * {
              /* Contain styles within iframe */
              contain: style;
            }
          </style>
        </head>
        <body>
          <div class="email-content">
            ${htmlContent}
          </div>
        </body>
        </html>
      `
      
      iframeDoc.open()
      iframeDoc.write(isolatedHTML)
      iframeDoc.close()
      
      // Resize iframe to content height
      const resizeIframe = () => {
        try {
          const height = iframeDoc.body.scrollHeight
          iframe.style.height = height + 'px'
        } catch (e) {
          // Fallback height if we can't access iframe content
          iframe.style.height = '400px'
        }
      }
      
      // Initial resize
      setTimeout(resizeIframe, 100)
      
      // Resize on window resize
      window.addEventListener('resize', resizeIframe)
      
      return () => {
        window.removeEventListener('resize', resizeIframe)
      }
    }
  }, [htmlContent, activeTab])

  if (activeTab === 'text' && textContent) {
    return (
      <div className="fi-email-text-content whitespace-pre-wrap font-mono text-sm leading-relaxed">
        {textContent}
      </div>
    )
  }

  if (activeTab === 'html' && htmlContent) {
    return (
      <iframe
        ref={iframeRef}
        className="fi-email-html-iframe w-full border-0 bg-transparent"
        style={{ minHeight: '200px' }}
        sandbox="allow-same-origin"
        title="Email Content"
      />
    )
  }

  return (
    <div className="fi-email-fallback text-muted-foreground text-center py-8">
      <div className="text-lg mb-2">No Content Available</div>
      <div className="text-sm">This email may not have readable content or it hasn't been fully synced yet.</div>
    </div>
  )
}

export default EmailContentViewer 