import { TextField, TextFieldProps } from '@mui/material'
import { UseFormRegisterReturn } from 'react-hook-form'

interface FormFieldProps extends Omit<TextFieldProps, 'error' | 'helperText'> {
  register?: UseFormRegisterReturn
  errorMessage?: string
}

export default function FormField({ register, errorMessage, ...props }: FormFieldProps) {
  return (
    <TextField
      {...props}
      {...register}
      error={!!errorMessage}
      helperText={errorMessage}
      fullWidth
      margin="normal"
    />
  )
}
