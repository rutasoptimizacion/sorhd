/**
 * PatientNavigator - Navegación para paciente
 */

import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import {PatientStackParamList} from './types';
import {VisitStatusScreen} from '../screens/patient/VisitStatusScreen';

const Stack = createStackNavigator<PatientStackParamList>();

export const PatientNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false, // Sin header por ahora
      }}>
      <Stack.Screen name="VisitStatus" component={VisitStatusScreen} />
      {/* Fase 3: Agregar más pantallas */}
    </Stack.Navigator>
  );
};
