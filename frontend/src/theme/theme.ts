import { createTheme } from '@mui/material/styles'

/** Clean TÜV-style business theme: white/gray surfaces with blue accent. */
export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#0057A8',
      light: '#2E7BC4',
      dark: '#003D75',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#4A5568',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F2F4F7',
      paper: '#FFFFFF',
    },
    divider: '#D8DEE6',
    text: {
      primary: '#1A2332',
      secondary: '#5A6878',
    },
    success: { main: '#1B7A4E' },
    warning: { main: '#B86E00' },
    error: { main: '#C62828' },
  },
  typography: {
    fontFamily: '"IBM Plex Sans", "Helvetica Neue", Arial, sans-serif',
    h4: { fontWeight: 700, letterSpacing: '-0.02em' },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 6 },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          boxShadow: '0 1px 0 #D8DEE6',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: '1px solid #D8DEE6',
          backgroundColor: '#FFFFFF',
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { borderRadius: 4 },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            fontWeight: 600,
            backgroundColor: '#EEF2F6',
            color: '#1A2332',
          },
        },
      },
    },
    MuiPaper: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          border: '1px solid #D8DEE6',
        },
      },
    },
  },
})
