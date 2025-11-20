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
import {useNavigation} from '@react-navigation/native';
import {StackNavigationProp} from '@react-navigation/stack';
import {useAuth} from '../../contexts/AuthContext';
import {BigText, BigButton, ErrorAlert} from '../../components';
import {elderlyTheme} from '../../theme/elderlyTheme';
import {RootStackParamList} from '../../types';

type LoginScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Login'>;

const LoginScreen: React.FC = () => {
  const navigation = useNavigation<LoginScreenNavigationProp>();
  const {login} = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isValid = username.length >= 3 && password.length >= 8;

  const handleLogin = async () => {
    if (!isValid) {
      setError('Usuario debe tener al menos 3 caracteres y contraseña 8 caracteres');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await login({username, password});

      // La navegación se maneja automáticamente por AppNavigator
      // basado en el estado de autenticación del AuthContext
    } catch (err: any) {
      console.error('Error en login:', err);

      // Extraer mensaje de error de forma segura
      let errorMessage = 'Error al iniciar sesión. Verifique sus credenciales.';

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
          <BigText variant="xxxl" style={styles.logo}>
            🏥
          </BigText>
          <BigText variant="xl" weight="bold" style={styles.title}>
            SOR-HD
          </BigText>
          <BigText variant="md" color={elderlyTheme.colors.textSecondary}>
            Sistema de Rutas
          </BigText>
        </View>

        <View style={styles.form}>
          <BigText variant="md" weight="medium" style={styles.label}>
            Usuario
          </BigText>
          <TextInput
            style={styles.input}
            value={username}
            onChangeText={setUsername}
            placeholder="Ingrese su usuario"
            placeholderTextColor={elderlyTheme.colors.textTertiary}
            autoCapitalize="none"
            autoCorrect={false}
            editable={!loading}
            accessibilityLabel="Campo de usuario"
          />

          <BigText variant="md" weight="medium" style={styles.label}>
            Contraseña
          </BigText>
          <View style={styles.passwordContainer}>
            <TextInput
              style={[styles.input, styles.passwordInput]}
              value={password}
              onChangeText={setPassword}
              placeholder="Ingrese su contraseña"
              placeholderTextColor={elderlyTheme.colors.textTertiary}
              secureTextEntry={!showPassword}
              autoCapitalize="none"
              autoCorrect={false}
              editable={!loading}
              accessibilityLabel="Campo de contraseña"
            />
            <TouchableOpacity
              style={styles.eyeButton}
              onPress={() => setShowPassword(!showPassword)}
              accessibilityLabel={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}>
              <BigText variant="lg">{showPassword ? '👁️' : '👁️‍🗨️'}</BigText>
            </TouchableOpacity>
          </View>

          {error && (
            <ErrorAlert
              message={error}
              onDismiss={() => setError(null)}
              onRetry={handleLogin}
            />
          )}

          <BigButton
            title="INICIAR SESIÓN"
            variant="primary"
            onPress={handleLogin}
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
  logo: {
    marginBottom: elderlyTheme.spacing.sm,
  },
  title: {
    marginBottom: elderlyTheme.spacing.xs,
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
    paddingRight: 60, // Espacio para el botón del ojo
  },
  eyeButton: {
    position: 'absolute',
    right: elderlyTheme.spacing.sm,
    top: 0,
    bottom: 0,
    justifyContent: 'center',
    paddingHorizontal: elderlyTheme.spacing.sm,
  },
  button: {
    marginTop: elderlyTheme.spacing.lg,
  },
});

export default LoginScreen;
