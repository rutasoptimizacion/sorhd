import React, {useState} from 'react';
import {
  View,
  TextInput,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import {useAuth} from '../../contexts/AuthContext';
import {BigText, BigButton, ErrorAlert} from '../../components';
import {elderlyTheme} from '../../theme/elderlyTheme';

const ActivationScreen: React.FC = () => {
  const {user, activate} = useAuth();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isLengthValid = newPassword.length >= 8;
  const doPasswordsMatch = newPassword === confirmPassword && newPassword.length > 0;
  const isValid = isLengthValid && doPasswordsMatch;

  const handleActivation = async () => {
    if (!isValid) {
      setError('Por favor complete todos los requisitos');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await activate({new_password: newPassword});

      // La navegación se maneja automáticamente por AppNavigator
    } catch (err: any) {
      console.error('Error en activación:', err);

      // Extraer mensaje de error de forma segura
      let errorMessage = 'Error al activar la cuenta. Intente nuevamente.';

      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        // Si detail es un objeto (validación Pydantic), convertir a string
        if (typeof detail === 'object') {
          errorMessage = JSON.stringify(detail);
        } else {
          errorMessage = String(detail);
        }
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'android' ? 'height' : 'padding'}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <BigText variant="xxxl" style={styles.icon}>
            ⚠️
          </BigText>
          <BigText variant="xl" weight="bold" style={styles.title}>
            ACTIVACIÓN DE CUENTA
          </BigText>
          <BigText variant="lg" style={styles.subtitle}>
            Bienvenido, {user?.username}
          </BigText>
          <BigText
            variant="md"
            color={elderlyTheme.colors.textSecondary}
            style={styles.description}>
            Por favor establezca una contraseña permanente
          </BigText>
        </View>

        <View style={styles.form}>
          <BigText variant="md" weight="medium" style={styles.label}>
            Nueva Contraseña
          </BigText>
          <View style={styles.passwordContainer}>
            <TextInput
              style={[styles.input, styles.passwordInput]}
              value={newPassword}
              onChangeText={setNewPassword}
              placeholder="Mínimo 8 caracteres"
              placeholderTextColor={elderlyTheme.colors.textTertiary}
              secureTextEntry={!showNewPassword}
              autoCapitalize="none"
              autoCorrect={false}
              editable={!loading}
              accessibilityLabel="Campo de nueva contraseña"
            />
            <TouchableOpacity
              style={styles.eyeButton}
              onPress={() => setShowNewPassword(!showNewPassword)}
              accessibilityLabel={
                showNewPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'
              }>
              <BigText variant="lg">{showNewPassword ? '👁️' : '👁️‍🗨️'}</BigText>
            </TouchableOpacity>
          </View>

          <BigText variant="md" weight="medium" style={styles.label}>
            Confirmar Contraseña
          </BigText>
          <View style={styles.passwordContainer}>
            <TextInput
              style={[styles.input, styles.passwordInput]}
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              placeholder="Repita su contraseña"
              placeholderTextColor={elderlyTheme.colors.textTertiary}
              secureTextEntry={!showConfirmPassword}
              autoCapitalize="none"
              autoCorrect={false}
              editable={!loading}
              accessibilityLabel="Campo de confirmar contraseña"
            />
            <TouchableOpacity
              style={styles.eyeButton}
              onPress={() => setShowConfirmPassword(!showConfirmPassword)}
              accessibilityLabel={
                showConfirmPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'
              }>
              <BigText variant="lg">{showConfirmPassword ? '👁️' : '👁️‍🗨️'}</BigText>
            </TouchableOpacity>
          </View>

          <View style={styles.validationContainer}>
            <View style={styles.validationRow}>
              <BigText variant="lg" style={styles.checkIcon}>
                {isLengthValid ? '✅' : '⭕'}
              </BigText>
              <BigText
                variant="sm"
                color={
                  isLengthValid ? elderlyTheme.colors.success : elderlyTheme.colors.textSecondary
                }>
                Al menos 8 caracteres
              </BigText>
            </View>
            <View style={styles.validationRow}>
              <BigText variant="lg" style={styles.checkIcon}>
                {doPasswordsMatch ? '✅' : '⭕'}
              </BigText>
              <BigText
                variant="sm"
                color={
                  doPasswordsMatch ? elderlyTheme.colors.success : elderlyTheme.colors.textSecondary
                }>
                Contraseñas coinciden
              </BigText>
            </View>
          </View>

          {error && (
            <ErrorAlert
              message={error}
              onDismiss={() => setError(null)}
              onRetry={handleActivation}
            />
          )}

          <BigButton
            title="ACTIVAR CUENTA"
            variant="success"
            onPress={handleActivation}
            loading={loading}
            disabled={!isValid || loading}
            fullWidth
            style={styles.button}
          />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: elderlyTheme.colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: elderlyTheme.spacing.lg,
  },
  header: {
    alignItems: 'center',
    marginBottom: elderlyTheme.spacing.xl,
  },
  icon: {
    marginBottom: elderlyTheme.spacing.sm,
  },
  title: {
    marginBottom: elderlyTheme.spacing.sm,
    textAlign: 'center',
  },
  subtitle: {
    marginBottom: elderlyTheme.spacing.xs,
  },
  description: {
    textAlign: 'center',
  },
  form: {
    width: '100%',
  },
  label: {
    marginBottom: elderlyTheme.spacing.xs,
    marginTop: elderlyTheme.spacing.md,
  },
  input: {
    minHeight: elderlyTheme.input.minHeight,
    fontSize: elderlyTheme.input.fontSize,
    paddingHorizontal: elderlyTheme.input.paddingHorizontal,
    paddingVertical: elderlyTheme.input.paddingVertical,
    borderWidth: elderlyTheme.input.borderWidth,
    borderColor: elderlyTheme.colors.border,
    borderRadius: elderlyTheme.borderRadius.medium,
    backgroundColor: elderlyTheme.colors.surface,
    color: elderlyTheme.colors.text,
  },
  passwordContainer: {
    position: 'relative',
  },
  passwordInput: {
    paddingRight: 60,
  },
  eyeButton: {
    position: 'absolute',
    right: elderlyTheme.spacing.sm,
    top: 0,
    bottom: 0,
    justifyContent: 'center',
    paddingHorizontal: elderlyTheme.spacing.sm,
  },
  validationContainer: {
    marginTop: elderlyTheme.spacing.md,
    padding: elderlyTheme.spacing.md,
    backgroundColor: elderlyTheme.colors.surface,
    borderRadius: elderlyTheme.borderRadius.medium,
  },
  validationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: elderlyTheme.spacing.xs,
  },
  checkIcon: {
    marginRight: elderlyTheme.spacing.sm,
  },
  button: {
    marginTop: elderlyTheme.spacing.lg,
  },
});

export default ActivationScreen;
