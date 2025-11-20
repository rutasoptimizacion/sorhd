import React from 'react';
import {View, StyleSheet} from 'react-native';
import {useAuth} from '../contexts/AuthContext';
import {BigText, BigButton} from '../components';
import {elderlyTheme} from '../theme/elderlyTheme';

const AdminScreen: React.FC = () => {
  const {user, logout} = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <View style={styles.container}>
      <BigText variant="xxxl" style={styles.icon}>
        👨‍💼
      </BigText>
      <BigText variant="xl" weight="bold" style={styles.title}>
        Panel de Administración
      </BigText>
      <BigText variant="lg" style={styles.subtitle}>
        Bienvenido, {user?.full_name || user?.username}
      </BigText>
      <BigText
        variant="md"
        color={elderlyTheme.colors.textSecondary}
        style={styles.message}>
        La aplicación móvil está diseñada para el personal clínico y pacientes.
      </BigText>
      <BigText
        variant="md"
        color={elderlyTheme.colors.textSecondary}
        style={styles.message}>
        Para acceder al panel de administración, por favor utilice la interfaz
        web en su computadora.
      </BigText>

      <BigButton
        title="CERRAR SESIÓN"
        variant="error"
        onPress={handleLogout}
        fullWidth
        style={styles.button}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: elderlyTheme.colors.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: elderlyTheme.spacing.xl,
  },
  icon: {
    marginBottom: elderlyTheme.spacing.md,
  },
  title: {
    marginBottom: elderlyTheme.spacing.sm,
    textAlign: 'center',
  },
  subtitle: {
    marginBottom: elderlyTheme.spacing.lg,
    color: elderlyTheme.colors.primary,
    textAlign: 'center',
  },
  message: {
    textAlign: 'center',
    marginBottom: elderlyTheme.spacing.md,
  },
  button: {
    marginTop: elderlyTheme.spacing.xl,
  },
});

export default AdminScreen;
