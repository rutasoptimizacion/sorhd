import { useLocation, useNavigate } from 'react-router-dom'
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Divider,
  Box,
} from '@mui/material'
import {
  Dashboard,
  People,
  DirectionsCar,
  PersonPin,
  MedicalServices,
  Route,
  Map,
  Notifications,
  Assessment,
  Build,
  LocalHospital,
  Assignment,
  ManageAccounts,
} from '@mui/icons-material'

const drawerWidth = 240

interface SidebarProps {
  mobileOpen: boolean
  onMobileClose: () => void
}

const menuItems = [
  { text: 'Panel Principal', icon: <Dashboard />, path: '/' },
  { text: 'Usuarios', icon: <ManageAccounts />, path: '/users' },
  { text: 'Habilidades', icon: <Build />, path: '/skills' },
  { text: 'Tipos de Atención', icon: <LocalHospital />, path: '/care-types' },
  { text: 'Personal', icon: <People />, path: '/personnel' },
  { text: 'Vehículos', icon: <DirectionsCar />, path: '/vehicles' },
  { text: 'Pacientes', icon: <PersonPin />, path: '/patients' },
  { text: 'Casos', icon: <MedicalServices />, path: '/cases' },
  { text: 'Planificación', icon: <Route />, path: '/planning' },
  { text: 'Rutas', icon: <Assignment />, path: '/routes' },
  { text: 'Monitoreo en Vivo', icon: <Map />, path: '/monitoring' },
  { text: 'Notificaciones', icon: <Notifications />, path: '/notifications' },
  { text: 'Reportes', icon: <Assessment />, path: '/reports' },
]

export default function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  const location = useLocation()
  const navigate = useNavigate()

  const handleNavigation = (path: string) => {
    navigate(path)
    onMobileClose()
  }

  const drawerContent = (
    <Box>
      <Toolbar />
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  )

  return (
    <Box component="nav" sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}>
      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onMobileClose}
        ModalProps={{
          keepMounted: true, // Better performance on mobile
        }}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', sm: 'block' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
        }}
        open
      >
        {drawerContent}
      </Drawer>
    </Box>
  )
}
