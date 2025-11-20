import { Alert, AlertTitle, Box } from '@mui/material'

interface ErrorMessageProps {
  title?: string
  message: string
  onRetry?: () => void
}

export default function ErrorMessage({ title = 'Error', message, onRetry }: ErrorMessageProps) {
  return (
    <Box sx={{ my: 2 }}>
      <Alert severity="error" onClose={onRetry ? onRetry : undefined}>
        <AlertTitle>{title}</AlertTitle>
        {message}
      </Alert>
    </Box>
  )
}
