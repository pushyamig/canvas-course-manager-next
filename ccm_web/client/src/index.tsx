import { SnackbarProvider } from 'notistack'
import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Switch } from 'react-router-dom'
import { ThemeProvider, StyledEngineProvider } from '@mui/material'

import App from './App.js'
import './index.css'
import ccmTheme from './theme.js'
import AccessDenied from './pages/AccessDenied.js'
import LaunchError from './pages/LaunchError.js'

const helpContactProps = {
  email: '4help@umich.edu',
  helpLink: 'https://its.umich.edu/help'
}

const root = createRoot(document.getElementById('root') as Element)
root.render(
  <React.StrictMode>
   <StyledEngineProvider injectFirst>
     <ThemeProvider theme={ccmTheme}>
      <SnackbarProvider maxSnack={3}>
        <BrowserRouter>
          <Switch>
            <Route exact={true} path='/access-denied'>
              <AccessDenied {...helpContactProps} />
            </Route>
            <Route exact={true} path='/launch-error'>
              <LaunchError {...helpContactProps} />
            </Route>
            <Route><App /></Route>
          </Switch>
        </BrowserRouter>
      </SnackbarProvider>
     </ThemeProvider>
   </StyledEngineProvider>
  </React.StrictMode>
)
