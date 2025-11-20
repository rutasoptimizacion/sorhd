/**
 * ClinicalNavigator - Navegación para equipo clínico
 */

import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import {ClinicalStackParamList} from './types';
import {RouteListScreen} from '../screens/clinical/RouteListScreen';

const Stack = createStackNavigator<ClinicalStackParamList>();

export const ClinicalNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false, // Sin header por ahora, para adultos mayores preferimos navegación simple
      }}>
      <Stack.Screen name="RouteList" component={RouteListScreen} />
      {/* Fase 3: Agregar más pantallas */}
    </Stack.Navigator>
  );
};
