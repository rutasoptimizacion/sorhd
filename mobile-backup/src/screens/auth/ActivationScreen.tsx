/**
 * ActivationScreen - Pantalla de activación de cuenta (primera vez)
 *
 * Permite al usuario establecer su contraseña permanente
 * cuando first_login === 1
 */

import React, {useState} from 'react';
import {
  View,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import {elderlyTheme} from '../../theme/elderlyTheme';
import {BigText, BigButton} from '../../components';
import {useAuth} from '../../contexts/AuthContext';
import {authService} from '../../api/services/authService';

interface ActivationScreenProps {
  navigation: any;
}

export const ActivationScreen: React.FC<ActivationScreenProps> = ({navigation}) => {
  const {user, activate} = useAuth();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Validaciones en tiempo real
  const isMinLength = newPassword.length >= 8;
  const passwordsMatch = newPassword === confirmPassword && confirmPassword.length > 0;
  const isValid = isMinLength && passwordsMatch;

  const handleActivate = async () => {
    if (!isValid) {
      setError('Por favor complete todos los requisitos');
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      // Llamar al endpoint de activación
      const response = await authService.activateAccount(newPassword);

      // Actualizar contexto con el usuario activado
      await activate(response.tokens, response.user);

      // El AppNavigator redirigirá según el rol
    } catch (err: any) {
      console.error('Activation error:', err);
      const errorMessage =
        err.response?.data?.detail || err.message || 'Error al activar la cuenta';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled">
        {/* Header con ícono y título */}
        <View style={styles.header}>
          <BigText variant="xxl" style={styles.icon}>
            ⚠️
          </BigText>
          <BigText variant="xl" weight="bold" textAlign="center" color={elderlyTheme.colors.warning}>
            ACTIVACIÓN DE CUENTA
          </BigText>
          <View style={styles.welcomeContainer}>
            <BigText variant="lg" textAlign="center" style={styles.welcome}>
              Bienvenido, {user?.full_name || user?.username}
            </BigText>
            <BigText
              variant="md"
              color={elderlyTheme.colors.textSecondary}
              textAlign="center"
              style={styles.subtitle}>
              Por favor establezca una contraseña permanente
            </BigText>
          </View>
        </View>

        {/* Formulario */}
        <View style={styles.form}>
          {/* Input Nueva Contraseña */}
          <View style={styles.inputGroup}>
            <BigText variant="md" weight="semibold" style={styles.label}>
              Nueva Contraseña
            </BigText>
            <View style={styles.passwordContainer}>
              <TextInput
                style={[styles.input, styles.passwordInput]}
                value={newPassword}
                onChangeText={setNewPassword}
                placeholder="Mínimo 8 caracteres"
                placeholderTextColor={elderlyTheme.colors.disabled}
                secureTextEntry={!showNewPassword}
                autoCapitalize="none"
                autoCorrect={false}
                editable={!isLoading}
                accessibilityLabel="Campo de nueva contraseña"
              />
              <TouchableOpacity
                style={styles.eyeButton}
                onPress={() => setShowNewPassword(!showNewPassword)}
                accessibilityLabel={showNewPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}>
                <BigText variant="lg">{showNewPassword ? '👁️' : '👁️‍🗨️'}</BigText>
              </TouchableOpacity>
            </View>
          </View>

          {/* Input Confirmar Contraseña */}
          <View style={styles.inputGroup}>
            <BigText variant="md" weight="semibold" style={styles.label}>
              Confirmar Contraseña
            </BigText>
            <View style={styles.passwordContainer}>
              <TextInput
                style={[styles.input, styles.passwordInput]}
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                placeholder="Repita la contraseña"
                placeholderTextColor={elderlyTheme.colors.disabled}
                secureTextEntry={!showConfirmPassword}
                autoCapitalize="none"
                autoCorrect={false}
                editable={!isLoading}
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
          </View>

          {/* Validaciones visuales */}
          <View style={styles.validations}>
            <View style={styles.validationItem}>
              <BigText
                variant="md"
                color={isMinLength ? elderlyTheme.colors.success : elderlyTheme.colors.disabled}>
                {isMinLength ? '✓' : '○'}
              </BigText>
              <BigText
                variant="md"
                color={isMinLength ? elderlyTheme.colors.success : elderlyTheme.colors.textSecondary}
                style={styles.validationText}>
                Al menos 8 caracteres
              </BigText>
            </View>
            <View style={styles.validationItem}>
              <BigText
                variant="md"
                color={passwordsMatch ? elderlyTheme.colors.success : elderlyTheme.colors.disabled}>
                {passwordsMatch ? '✓' : '○'}
              </BigText>
              <BigText
                variant="md"
                color={
                  passwordsMatch ? elderlyTheme.colors.success : elderlyTheme.colors.textSecondary
                }
                style={styles.validationText}>
                Las contraseñas coinciden
              </BigText>
            </View>
          </View>

          {/* Mensaje de error */}
          {error ? (
            <View style={styles.errorContainer}>
              <BigText variant="md" color={elderlyTheme.colors.error} textAlign="center">
                {error}
              </BigText>
            </View>
          ) : null}

          {/* Botón Activar */}
          <BigButton
            title="ACTIVAR CUENTA"
            onPress={handleActivate}
            variant="primary"
            loading={isLoading}
            disabled={!isValid || isLoading}
            style={styles.activateButton}
            accessibilityHint="Toca para activar tu cuenta con la nueva contraseña"
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
    padding: elderlyTheme.spacing.lg,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: elderlyTheme.spacing.xl,
  },
  icon: {
    fontSize: elderlyTheme.icon.xlarge,
    marginBottom: elderlyTheme.spacing.md,
  },
  welcomeContainer: {
    marginTop: elderlyTheme.spacing.lg,
  },
  welcome: {
    marginBottom: elderlyTheme.spacing.sm,
  },
  subtitle: {
    marginTop: elderlyTheme.spacing.xs,
  },
  form: {
    width: '100%',
  },
  inputGroup: {
    marginBottom: elderlyTheme.spacing.lg,
  },
  label: {
    marginBottom: elderlyTheme.spacing.xs,
  },
  input: {
    height: elderlyTheme.button.minHeight,
    borderWidth: 2,
    borderColor: elderlyTheme.colors.textSecondary,
    borderRadius: 8,
    paddingHorizontal: elderlyTheme.spacing.md,
    fontSize: elderlyTheme.fontSize.md,
    color: elderlyTheme.colors.text,
    backgroundColor: elderlyTheme.colors.background,
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
    padding: elderlyTheme.spacing.sm,
  },
  validations: {
    marginBottom: elderlyTheme.spacing.lg,
  },
  validationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: elderlyTheme.spacing.sm,
  },
  validationText: {
    marginLeft: elderlyTheme.spacing.sm,
  },
  errorContainer: {
    marginBottom: elderlyTheme.spacing.md,
    padding: elderlyTheme.spacing.md,
    backgroundColor: '#FFEBEE',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: elderlyTheme.colors.error,
  },
  activateButton: {
    marginTop: elderlyTheme.spacing.md,
  },
});
