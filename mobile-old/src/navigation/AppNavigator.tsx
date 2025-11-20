/**
 * AppNavigator - Navegación principal de la aplicación
 *
 * Estructura:
 * - AuthStack: Login, Activation (no autenticado o necesita activación)
 * - MainStack: ClinicalStack o PatientStack (autenticado)
 */

import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createStackNavigator} from '@react-navigation/stack';
import {AuthStackParamList} from './types';
import {useAuth} from '../contexts/AuthContext';
import {LoadingSpinner} from '../components';

// Pantallas de autenticación
import {LoginScreen} from '../screens/auth/LoginScreen';
import {ActivationScreen} from '../screens/auth/ActivationScreen';

// Navegadores por rol
import {ClinicalNavigator} from './ClinicalNavigator';
import {PatientNavigator} from './PatientNavigator';

const AuthStack = createStackNavigator<AuthStackParamList>();

export const AppNavigator: React.FC = () => {
  const {isAuthenticated, needsActivation, user, isLoading} = useAuth();

  // Mostrar spinner mientras carga el estado de autenticación
  if (isLoading) {
    return <LoadingSpinner size="large" message="Cargando..." />;
  }

  return (
    <NavigationContainer>
      {!isAuthenticated ? (
        // Usuario no autenticado → AuthStack
        <AuthStack.Navigator screenOptions={{headerShown: false}}>
          <AuthStack.Screen name="Login" component={LoginScreen} />
          <AuthStack.Screen name="Activation" component={ActivationScreen} />
        </AuthStack.Navigator>
      ) : needsActivation ? (
        // Usuario autenticado pero necesita activar cuenta
        <AuthStack.Navigator screenOptions={{headerShown: false}}>
          <AuthStack.Screen name="Activation" component={ActivationScreen} />
        </AuthStack.Navigator>
      ) : (
        // Usuario autenticado y activado → MainStack según rol
        renderMainStack(user?.role)
      )}
    </NavigationContainer>
  );
};

/**
 * Renderiza el navegador correspondiente según el rol del usuario
 */
const renderMainStack = (role?: string) => {
  if (role === 'clinical_team') {
    return <ClinicalNavigator />;
  } else if (role === 'patient') {
    return <PatientNavigator />;
  }

  // Si el rol no es reconocido, mostrar error
  return (
    <LoadingSpinner
      size="large"
      message="Error: Rol de usuario no reconocido"
    />
  );
};
