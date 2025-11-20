/**
 * LoginScreen - Pantalla de inicio de sesión
 *
 * Características para adultos mayores:
 * - Textos grandes (22pt base)
 * - Inputs grandes (56dp altura)
 * - Botones grandes con fuente 20pt
 * - Alto contraste (WCAG AAA)
 * - Mensajes de error claros
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
  Alert,
} from 'react-native';
import {elderlyTheme} from '../../theme/elderlyTheme';
import {BigText, BigButton, ErrorAlert} from '../../components';
import {useAuth} from '../../contexts/AuthContext';
import {authService} from '../../api/services/authService';

interface LoginScreenProps {
  navigation: any; // TODO: tipar correctamente con NavigationProp
}

export const LoginScreen: React.FC<LoginScreenProps> = ({navigation}) => {
  const {login} = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async () => {
    // Validación
    if (!username.trim()) {
      setError('Por favor ingrese su usuario');
      return;
    }
    if (username.trim().length < 3) {
      setError('El usuario debe tener al menos 3 caracteres');
      return;
    }
    if (!password) {
      setError('Por favor ingrese su contraseña');
      return;
    }
    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres');
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      // Llamar al servicio de autenticación
      const response = await authService.login(username.trim(), password);

      // Guardar en contexto
      await login(response.tokens, response.user);

      // Si first_login === 1, navegar a ActivationScreen
      if (response.user.first_login === 1) {
        navigation.replace('Activation');
      }
      // Si no, el AppNavigator lo redirigirá según el rol
    } catch (err: any) {
      console.error('Login error:', err);
      const errorMessage =
        err.response?.data?.detail || err.message || 'Error al iniciar sesión';
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
        {/* Logo y título */}
        <View style={styles.header}>
          <BigText variant="xxl" weight="bold" textAlign="center" style={styles.logo}>
            🏥
          </BigText>
          <BigText variant="xl" weight="bold" textAlign="center">
            SOR-HD
          </BigText>
          <BigText
            variant="lg"
            color={elderlyTheme.colors.textSecondary}
            textAlign="center"
            style={styles.subtitle}>
            Sistema de Rutas
          </BigText>
        </View>

        {/* Formulario */}
        <View style={styles.form}>
          {/* Input Usuario */}
          <View style={styles.inputGroup}>
            <BigText variant="md" weight="semibold" style={styles.label}>
              Usuario
            </BigText>
            <TextInput
              style={styles.input}
              value={username}
              onChangeText={setUsername}
              placeholder="Ingrese su usuario"
              placeholderTextColor={elderlyTheme.colors.disabled}
              autoCapitalize="none"
              autoCorrect={false}
              editable={!isLoading}
              accessibilityLabel="Campo de usuario"
              accessibilityHint="Ingrese su nombre de usuario"
            />
          </View>

          {/* Input Contraseña */}
          <View style={styles.inputGroup}>
            <BigText variant="md" weight="semibold" style={styles.label}>
              Contraseña
            </BigText>
            <View style={styles.passwordContainer}>
              <TextInput
                style={[styles.input, styles.passwordInput]}
                value={password}
                onChangeText={setPassword}
                placeholder="Ingrese su contraseña"
                placeholderTextColor={elderlyTheme.colors.disabled}
                secureTextEntry={!showPassword}
                autoCapitalize="none"
                autoCorrect={false}
                editable={!isLoading}
                accessibilityLabel="Campo de contraseña"
                accessibilityHint="Ingrese su contraseña"
              />
              <TouchableOpacity
                style={styles.eyeButton}
                onPress={() => setShowPassword(!showPassword)}
                accessibilityLabel={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}>
                <BigText variant="lg">{showPassword ? '👁️' : '👁️‍🗨️'}</BigText>
              </TouchableOpacity>
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

          {/* Botón Iniciar Sesión */}
          <BigButton
            title="INICIAR SESIÓN"
            onPress={handleLogin}
            variant="primary"
            loading={isLoading}
            disabled={isLoading}
            style={styles.loginButton}
            accessibilityHint="Toca para iniciar sesión con tus credenciales"
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
  logo: {
    fontSize: 80,
    marginBottom: elderlyTheme.spacing.md,
  },
  subtitle: {
    marginTop: elderlyTheme.spacing.sm,
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
    paddingRight: 60, // Espacio para el botón del ojo
  },
  eyeButton: {
    position: 'absolute',
    right: elderlyTheme.spacing.sm,
    top: 0,
    bottom: 0,
    justifyContent: 'center',
    padding: elderlyTheme.spacing.sm,
  },
  errorContainer: {
    marginBottom: elderlyTheme.spacing.md,
    padding: elderlyTheme.spacing.md,
    backgroundColor: '#FFEBEE',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: elderlyTheme.colors.error,
  },
  loginButton: {
    marginTop: elderlyTheme.spacing.md,
  },
});
