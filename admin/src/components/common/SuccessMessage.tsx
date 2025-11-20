import { Alert, AlertTitle, Snackbar } from '@mui/material'

interface SuccessMessageProps {
  title?: string
  message: string
  open: boolean
  onClose: () => void
  autoHideDuration?: number
}

export default function SuccessMessage({
  title = 'Éxito',
  message,
  open,
  onClose,
  autoHideDuration = 3000,
}: SuccessMessageProps) {
  return (
    <Snackbar open={open} autoHideDuration={autoHideDuration} onClose={onClose}>
      <Alert onClose={onClose} severity="success" sx={{ width: '100%' }}>
        {title && <AlertTitle>{title}</AlertTitle>}
        {message}
      </Alert>
    </Snackbar>
  )
}
