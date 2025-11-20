import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createStackNavigator} from '@react-navigation/stack';
import {useAuth} from '../contexts/AuthContext';
import {LoadingSpinner} from '../components';

// Screens (importaremos después de crearlas)
import LoginScreen from '../screens/auth/LoginScreen';
import ActivationScreen from '../screens/auth/ActivationScreen';
import AdminScreen from '../screens/AdminScreen';
import RouteListScreen from '../screens/clinical/RouteListScreen';
import VisitDetailScreen from '../screens/clinical/VisitDetailScreen';
import VisitStatusScreen from '../screens/patient/VisitStatusScreen';
import TeamInfoScreen from '../screens/patient/TeamInfoScreen';

import {RootStackParamList} from '../types';

const Stack = createStackNavigator<RootStackParamList>();

export const AppNavigator: React.FC = () => {
  const {isAuthenticated, needsActivation, user, isLoading} = useAuth();

  console.log('AppNavigator: isLoading=', isLoading, 'isAuthenticated=', isAuthenticated, 'user=', user?.username, 'role=', user?.role);

  if (isLoading) {
    return <LoadingSpinner size="large" message="Cargando..." />;
  }

  // Usuario no autenticado → AuthStack
  if (!isAuthenticated) {
    return (
      <NavigationContainer>
        <Stack.Navigator screenOptions={{headerShown: false}}>
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Activation" component={ActivationScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    );
  }

  // Usuario autenticado pero necesita activación → forzar ActivationScreen
  if (needsActivation) {
    return (
      <NavigationContainer>
        <Stack.Navigator screenOptions={{headerShown: false}}>
          <Stack.Screen name="Activation" component={ActivationScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    );
  }

  // Usuario autenticado y activado → MainStack según rol

  // Admin: mostrar mensaje informativo (no tiene pantallas móviles específicas)
  if (user?.role === 'admin') {
    return (
      <NavigationContainer>
        <Stack.Navigator
          screenOptions={{
            headerShown: true,
            headerStyle: {
              backgroundColor: '#1976D2',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
              fontSize: 20,
            },
          }}>
          <Stack.Screen
            name="RouteList"
            component={AdminScreen}
            options={{title: 'Administración'}}
          />
        </Stack.Navigator>
      </NavigationContainer>
    );
  }

  if (user?.role === 'clinical_team') {
    return (
      <NavigationContainer>
        <Stack.Navigator
          screenOptions={{
            headerShown: true,
            headerStyle: {
              backgroundColor: '#1976D2',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
              fontSize: 20,
            },
          }}>
          <Stack.Screen
            name="RouteList"
            component={RouteListScreen}
            options={{title: 'Mis Rutas'}}
          />
          <Stack.Screen
            name="VisitDetail"
            component={VisitDetailScreen}
            options={{title: 'Detalle de Visita'}}
          />
        </Stack.Navigator>
      </NavigationContainer>
    );
  }

  if (user?.role === 'patient') {
    return (
      <NavigationContainer>
        <Stack.Navigator
          screenOptions={{
            headerShown: true,
            headerStyle: {
              backgroundColor: '#1976D2',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
              fontSize: 20,
            },
          }}>
          <Stack.Screen
            name="VisitStatus"
            component={VisitStatusScreen}
            options={{title: 'Mi Visita'}}
          />
          <Stack.Screen
            name="TeamInfo"
            component={TeamInfoScreen}
            options={{title: 'Equipo Médico'}}
          />
        </Stack.Navigator>
      </NavigationContainer>
    );
  }

  // Rol no reconocido
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{headerShown: false}}>
        <Stack.Screen name="Login" component={LoginScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};
