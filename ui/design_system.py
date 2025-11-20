"""
PingMonitor Pro - Professional Design System
Centralized design tokens and component styles
"""


class DesignSystem:
    """
    Professional Design System
    All design tokens in one place for consistency
    """

    # ========================================
    # COLOR PALETTE
    # ========================================

    COLORS = {
        # Background
        'bg-primary': '#0f172a',      # Slate 950
        'bg-secondary': '#1e293b',    # Slate 800
        'bg-tertiary': '#334155',     # Slate 700
        'bg-hover': '#475569',        # Slate 600

        # Surface
        'surface-01': '#1e293b',
        'surface-02': '#334155',
        'surface-03': '#475569',

        # Border
        'border-subtle': '#334155',
        'border-default': '#475569',
        'border-strong': '#64748b',

        # Text
        'text-primary': '#f8fafc',    # Slate 50
        'text-secondary': '#cbd5e1',  # Slate 300
        'text-tertiary': '#94a3b8',   # Slate 400
        'text-disabled': '#64748b',   # Slate 500

        # Status - Online/Success
        'status-online': '#10b981',
        'status-online-bg': 'rgba(16, 185, 129, 0.1)',
        'status-online-border': 'rgba(16, 185, 129, 0.3)',

        # Status - Offline/Error
        'status-offline': '#ef4444',
        'status-offline-bg': 'rgba(239, 68, 68, 0.1)',
        'status-offline-border': 'rgba(239, 68, 68, 0.3)',

        # Status - Warning/Degraded
        'status-warning': '#f59e0b',
        'status-warning-bg': 'rgba(245, 158, 11, 0.1)',
        'status-warning-border': 'rgba(245, 158, 11, 0.3)',

        # Status - Info
        'status-info': '#3b82f6',
        'status-info-bg': 'rgba(59, 130, 246, 0.1)',
        'status-info-border': 'rgba(59, 130, 246, 0.3)',

        # Brand/Accent
        'brand-primary': '#6366f1',   # Indigo 500
        'brand-hover': '#4f46e5',     # Indigo 600
        'brand-active': '#4338ca',    # Indigo 700
        'brand-subtle': 'rgba(99, 102, 241, 0.1)',

        # Interactive
        'interactive-hover': 'rgba(255, 255, 255, 0.05)',
        'interactive-active': 'rgba(255, 255, 255, 0.1)',
        'focus-ring': '#6366f1',
    }

    # ========================================
    # TYPOGRAPHY
    # ========================================

    TYPOGRAPHY = {
        # Font Families
        'font-primary': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        'font-mono': 'JetBrains Mono, "SF Mono", Monaco, Consolas, "Courier New", monospace',

        # Font Sizes
        'text-xs': '11px',
        'text-sm': '13px',
        'text-base': '14px',
        'text-md': '16px',
        'text-lg': '18px',
        'text-xl': '20px',
        'text-2xl': '24px',
        'text-3xl': '32px',
        'text-4xl': '40px',

        # Font Weights
        'weight-regular': '400',
        'weight-medium': '500',
        'weight-semibold': '600',
        'weight-bold': '700',

        # Line Heights
        'leading-tight': '1.2',
        'leading-normal': '1.5',
        'leading-relaxed': '1.75',

        # Letter Spacing
        'tracking-tight': '-0.02em',
        'tracking-normal': '0',
        'tracking-wide': '0.025em',
        'tracking-wider': '0.05em',
    }

    # ========================================
    # SPACING
    # ========================================

    SPACING = {
        'space-0': '0px',
        'space-1': '4px',
        'space-2': '8px',
        'space-3': '12px',
        'space-4': '16px',
        'space-5': '20px',
        'space-6': '24px',
        'space-8': '32px',
        'space-10': '40px',
        'space-12': '48px',
        'space-16': '64px',
        'space-20': '80px',
    }

    # ========================================
    # BORDER RADIUS
    # ========================================

    RADIUS = {
        'radius-sm': '4px',
        'radius-md': '6px',
        'radius-lg': '8px',
        'radius-xl': '12px',
        'radius-2xl': '16px',
        'radius-full': '9999px',
    }

    # ========================================
    # SHADOWS
    # ========================================

    SHADOWS = {
        'shadow-xs': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'shadow-sm': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
        'shadow-md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
        'shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
        'shadow-xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
        'shadow-2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    }

    # ========================================
    # COMPONENT STYLES
    # ========================================

    @staticmethod
    def button_primary():
        """Primary button style"""
        return f"""
            QPushButton {{
                background-color: {DesignSystem.COLORS['brand-primary']};
                color: white;
                border: 1px solid {DesignSystem.COLORS['brand-primary']};
                border-radius: {DesignSystem.RADIUS['radius-md']};
                padding: 8px 16px;
                font-weight: {DesignSystem.TYPOGRAPHY['weight-medium']};
                font-size: {DesignSystem.TYPOGRAPHY['text-base']};
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {DesignSystem.COLORS['brand-hover']};
                border-color: {DesignSystem.COLORS['brand-hover']};
            }}
            QPushButton:pressed {{
                background-color: {DesignSystem.COLORS['brand-active']};
            }}
            QPushButton:disabled {{
                background-color: {DesignSystem.COLORS['bg-tertiary']};
                color: {DesignSystem.COLORS['text-disabled']};
                border-color: {DesignSystem.COLORS['border-subtle']};
            }}
        """

    @staticmethod
    def button_success():
        """Success button style"""
        return f"""
            QPushButton {{
                background-color: {DesignSystem.COLORS['status-online']};
                color: white;
                border: 1px solid {DesignSystem.COLORS['status-online']};
                border-radius: {DesignSystem.RADIUS['radius-md']};
                padding: 8px 16px;
                font-weight: {DesignSystem.TYPOGRAPHY['weight-medium']};
                font-size: {DesignSystem.TYPOGRAPHY['text-base']};
            }}
            QPushButton:hover {{
                background-color: #059669;
                border-color: #059669;
            }}
            QPushButton:disabled {{
                background-color: {DesignSystem.COLORS['bg-tertiary']};
                color: {DesignSystem.COLORS['text-disabled']};
            }}
        """

    @staticmethod
    def button_danger():
        """Danger button style"""
        return f"""
            QPushButton {{
                background-color: {DesignSystem.COLORS['status-offline']};
                color: white;
                border: 1px solid {DesignSystem.COLORS['status-offline']};
                border-radius: {DesignSystem.RADIUS['radius-md']};
                padding: 8px 16px;
                font-weight: {DesignSystem.TYPOGRAPHY['weight-medium']};
                font-size: {DesignSystem.TYPOGRAPHY['text-base']};
            }}
            QPushButton:hover {{
                background-color: #dc2626;
                border-color: #dc2626;
            }}
            QPushButton:disabled {{
                background-color: {DesignSystem.COLORS['bg-tertiary']};
                color: {DesignSystem.COLORS['text-disabled']};
            }}
        """

    @staticmethod
    def button_ghost():
        """Ghost button style"""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {DesignSystem.COLORS['text-secondary']};
                border: 1px solid transparent;
                border-radius: {DesignSystem.RADIUS['radius-md']};
                padding: 8px 16px;
                font-weight: {DesignSystem.TYPOGRAPHY['weight-medium']};
                font-size: {DesignSystem.TYPOGRAPHY['text-base']};
            }}
            QPushButton:hover {{
                background-color: {DesignSystem.COLORS['interactive-hover']};
                color: {DesignSystem.COLORS['text-primary']};
            }}
        """

    @staticmethod
    def card():
        """Card style"""
        return f"""
            QFrame {{
                background-color: {DesignSystem.COLORS['surface-01']};
                border: 1px solid {DesignSystem.COLORS['border-subtle']};
                border-radius: {DesignSystem.RADIUS['radius-xl']};
                padding: 20px;
            }}
        """

    @staticmethod
    def card_elevated():
        """Elevated card style"""
        return f"""
            QFrame {{
                background-color: {DesignSystem.COLORS['surface-02']};
                border: 1px solid {DesignSystem.COLORS['border-default']};
                border-radius: {DesignSystem.RADIUS['radius-xl']};
                padding: 20px;
            }}
        """

    @staticmethod
    def heading_1():
        """H1 heading style"""
        return f"""
            QLabel {{
                color: {DesignSystem.COLORS['text-primary']};
                font-size: {DesignSystem.TYPOGRAPHY['text-3xl']};
                font-weight: {DesignSystem.TYPOGRAPHY['weight-bold']};
                background: transparent;
            }}
        """

    @staticmethod
    def heading_2():
        """H2 heading style"""
        return f"""
            QLabel {{
                color: {DesignSystem.COLORS['text-primary']};
                font-size: {DesignSystem.TYPOGRAPHY['text-2xl']};
                font-weight: {DesignSystem.TYPOGRAPHY['weight-semibold']};
                background: transparent;
            }}
        """

    @staticmethod
    def heading_3():
        """H3 heading style"""
        return f"""
            QLabel {{
                color: {DesignSystem.COLORS['text-primary']};
                font-size: {DesignSystem.TYPOGRAPHY['text-lg']};
                font-weight: {DesignSystem.TYPOGRAPHY['weight-semibold']};
                background: transparent;
            }}
        """

    @staticmethod
    def text_secondary():
        """Secondary text style"""
        return f"""
            QLabel {{
                color: {DesignSystem.COLORS['text-tertiary']};
                font-size: {DesignSystem.TYPOGRAPHY['text-sm']};
                background: transparent;
            }}
        """

    @staticmethod
    def input_field():
        """Input field style"""
        return f"""
            QLineEdit {{
                background-color: {DesignSystem.COLORS['surface-01']};
                color: {DesignSystem.COLORS['text-primary']};
                border: 1px solid {DesignSystem.COLORS['border-subtle']};
                border-radius: {DesignSystem.RADIUS['radius-md']};
                padding: 8px 12px;
                selection-background-color: {DesignSystem.COLORS['brand-primary']};
            }}
            QLineEdit:hover {{
                border-color: {DesignSystem.COLORS['border-default']};
            }}
            QLineEdit:focus {{
                border-color: {DesignSystem.COLORS['focus-ring']};
                background-color: {DesignSystem.COLORS['bg-primary']};
            }}
        """

    @staticmethod
    def table_modern():
        """Modern table style"""
        return f"""
            QTableWidget {{
                background-color: {DesignSystem.COLORS['bg-primary']};
                alternate-background-color: {DesignSystem.COLORS['surface-01']};
                gridline-color: {DesignSystem.COLORS['border-subtle']};
                border: 1px solid {DesignSystem.COLORS['border-subtle']};
                border-radius: {DesignSystem.RADIUS['radius-lg']};
                selection-background-color: {DesignSystem.COLORS['brand-subtle']};
                selection-color: {DesignSystem.COLORS['text-primary']};
            }}
            QTableWidget::item {{
                padding: 12px;
                border: none;
                color: {DesignSystem.COLORS['text-secondary']};
            }}
            QTableWidget::item:hover {{
                background-color: {DesignSystem.COLORS['interactive-hover']};
            }}
            QHeaderView::section {{
                background-color: {DesignSystem.COLORS['surface-01']};
                color: {DesignSystem.COLORS['text-tertiary']};
                padding: 12px;
                border: none;
                border-bottom: 2px solid {DesignSystem.COLORS['border-subtle']};
                font-weight: {DesignSystem.TYPOGRAPHY['weight-semibold']};
                font-size: {DesignSystem.TYPOGRAPHY['text-sm']};
                text-transform: uppercase;
                letter-spacing: {DesignSystem.TYPOGRAPHY['tracking-wide']};
            }}
        """

    @staticmethod
    def status_badge(status='online'):
        """Status badge style"""
        status_map = {
            'online': ('status-online', 'status-online-bg', 'status-online-border'),
            'offline': ('status-offline', 'status-offline-bg', 'status-offline-border'),
            'degraded': ('status-warning', 'status-warning-bg', 'status-warning-border'),
            'warning': ('status-warning', 'status-warning-bg', 'status-warning-border'),
        }

        colors = status_map.get(status, status_map['online'])

        return f"""
            QFrame {{
                background-color: {DesignSystem.COLORS[colors[1]]};
                border: 1px solid {DesignSystem.COLORS[colors[0]]};
                border-radius: {DesignSystem.RADIUS['radius-xl']};
                padding: 6px 12px;
            }}
            QLabel {{
                color: {DesignSystem.COLORS[colors[0]]};
                font-weight: {DesignSystem.TYPOGRAPHY['weight-semibold']};
                font-size: {DesignSystem.TYPOGRAPHY['text-sm']};
            }}
        """


# Quick access helpers
DS = DesignSystem  # Shorthand alias
