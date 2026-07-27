import streamlit as st

def inject_custom_styles():
    """Inject premium, glassmorphic dark-mode CSS styles with emerald accents."""
    st.markdown(
        """
        <style>
        /* Base styles */
        .reportview-container {
            background: #09090b;
        }
        
        /* Glassmorphic cards */
        .glass-card {
            background: rgba(15, 15, 20, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }
        
        /* Metric box */
        .metric-box {
            text-align: center;
            padding: 15px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #10b981; /* Emerald-500 */
            font-family: monospace;
        }
        .metric-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #a1a1aa;
            margin-top: 4px;
        }
        
        /* Emerald Accent Buttons */
        .stButton>button {
            background-color: #10b981 !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 8px 16px !important;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #059669 !important; /* Emerald-600 */
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
        }
        
        /* Code fonts */
        code {
            color: #34d399 !important; /* Emerald-400 */
            background-color: rgba(255, 255, 255, 0.04) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_header(title: str, subtitle: str):
    """Renders a premium visual header with emerald elements."""
    st.markdown(
        f"""
        <div style="margin-bottom: 25px;">
            <h1 style="color: #ffffff; font-weight: 800; font-size: 2.2rem; margin-bottom: 5px;">
                <span style="color: #10b981;">NORAY</span> {title}
            </h1>
            <p style="color: #a1a1aa; font-size: 1rem; font-weight: 400; margin: 0;">
                {subtitle}
            </p>
            <hr style="border: 0; height: 1px; background: linear-gradient(to right, #10b981, rgba(255,255,255,0.05)); margin-top: 15px; margin-bottom: 20px;">
        </div>
        """,
        unsafe_allow_html=True
    )
