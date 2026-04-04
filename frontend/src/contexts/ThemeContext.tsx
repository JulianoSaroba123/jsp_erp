import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { getSettings, updateSettings } from '../api/settings';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('light');
  const [isLoading, setIsLoading] = useState(true);

  // Carregar tema salvo nas configurações
  useEffect(() => {
    const loadTheme = async () => {
      try {
        const settings = await getSettings();
        const savedTheme = settings.theme || 'light';
        setThemeState(savedTheme);
        applyTheme(savedTheme);
      } catch (error) {
        console.log('Usando tema padrão (light)');
        applyTheme('light');
      } finally {
        setIsLoading(false);
      }
    };
    loadTheme();
  }, []);

  const applyTheme = (newTheme: Theme) => {
    const root = document.documentElement;
    
    if (newTheme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  };

  const setTheme = async (newTheme: Theme) => {
    setThemeState(newTheme);
    applyTheme(newTheme);
    
    // Salvar nas configurações
    try {
      await updateSettings({ theme: newTheme });
    } catch (error) {
      console.error('Erro ao salvar tema:', error);
    }
  };

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  if (isLoading) {
    return null; // Ou um loading spinner
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
