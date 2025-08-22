#!/usr/bin/env python3
"""
Cloud debugging tool for Streamlit deployment issues
This will help identify exactly what's wrong in the cloud environment
"""

import streamlit as st
import os
import sys
from datetime import datetime

def debug_environment():
    """Debug the current environment and configuration"""
    
    st.title("🔧 Cloud Environment Debugger")
    st.markdown("*This tool helps identify configuration issues in cloud deployments*")
    
    # Environment Information
    with st.expander("🌍 Environment Information", expanded=True):
        st.markdown("**Python Version:**")
        st.code(f"{sys.version}")
        
        st.markdown("**Platform:**")
        st.code(f"{sys.platform}")
        
        st.markdown("**Current Working Directory:**")
        st.code(f"{os.getcwd()}")
        
        st.markdown("**Python Path:**")
        for path in sys.path[:5]:  # Show first 5 paths
            st.code(path)
    
    # Streamlit Secrets Debug
    with st.expander("🔑 Streamlit Secrets Debug", expanded=True):
        st.markdown("**Checking st.secrets availability:**")
        
        try:
            if hasattr(st, 'secrets'):
                st.success("✅ st.secrets is available")
                
                # Check if api_keys section exists
                if 'api_keys' in st.secrets:
                    st.success("✅ [api_keys] section found")
                    
                    # Check deepgram key
                    if 'deepgram' in st.secrets.api_keys:
                        deepgram_key = st.secrets.api_keys.deepgram
                        if deepgram_key == "your_deepgram_api_key_here":
                            st.error("❌ Deepgram key is placeholder value")
                        elif len(deepgram_key) > 10:
                            st.success(f"✅ Deepgram key found: {deepgram_key[:8]}...{deepgram_key[-4:]}")
                        else:
                            st.warning(f"⚠️ Deepgram key seems short: '{deepgram_key}'")
                    else:
                        st.error("❌ 'deepgram' key not found in api_keys")
                        st.info("Available keys in api_keys:")
                        for key in st.secrets.api_keys.keys():
                            st.code(f"- {key}")
                    
                    # Check speechify key
                    if 'speechify' in st.secrets.api_keys:
                        speechify_key = st.secrets.api_keys.speechify
                        st.success(f"✅ Speechify key found: {speechify_key[:8]}...{speechify_key[-4:]}")
                    else:
                        st.warning("⚠️ 'speechify' key not found in api_keys")
                else:
                    st.error("❌ [api_keys] section not found in secrets")
                    st.info("Available sections in secrets:")
                    try:
                        for section in st.secrets.keys():
                            st.code(f"- {section}")
                    except:
                        st.code("Cannot enumerate secrets sections")
                        
            else:
                st.error("❌ st.secrets is not available")
                
        except Exception as e:
            st.error(f"💥 Error accessing secrets: {e}")
    
    # Environment Variables Debug
    with st.expander("🌐 Environment Variables Debug"):
        st.markdown("**Checking environment variables:**")
        
        deepgram_env = os.getenv("DEEPGRAM_API_KEY")
        if deepgram_env:
            st.success(f"✅ DEEPGRAM_API_KEY env var: {deepgram_env[:8]}...{deepgram_env[-4:]}")
        else:
            st.info("ℹ️ No DEEPGRAM_API_KEY environment variable")
        
        # Check other relevant env vars
        relevant_vars = ["STREAMLIT_SERVER_PORT", "PYTHONPATH", "HOME", "USER"]
        for var in relevant_vars:
            value = os.getenv(var)
            if value:
                st.code(f"{var}: {value}")
    
    # API Key Resolution Test
    with st.expander("🧪 API Key Resolution Test", expanded=True):
        st.markdown("**Testing the actual API key resolution function:**")
        
        try:
            # Import the function
            sys.path.append('utils')
            from utils.nlp_processor import get_api_key_multi_source
            
            st.markdown("**Running get_api_key_multi_source('DEEPGRAM_API_KEY'):**")
            
            # Capture the result
            api_key = get_api_key_multi_source("DEEPGRAM_API_KEY")
            
            if api_key:
                if api_key == "your_deepgram_api_key_here":
                    st.error("❌ Function returned placeholder value")
                else:
                    st.success(f"✅ Function returned valid key: {api_key[:8]}...{api_key[-4:]}")
            else:
                st.error("❌ Function returned None/empty")
                
        except ImportError as e:
            st.error(f"💥 Import error: {e}")
        except Exception as e:
            st.error(f"💥 Execution error: {e}")
    
    # Deepgram API Test
    with st.expander("🎤 Deepgram API Connection Test"):
        st.markdown("**Testing actual Deepgram API connection:**")
        
        if st.button("🧪 Test Deepgram Connection"):
            try:
                sys.path.append('utils')
                from utils.nlp_processor import DeepgramVoice
                
                deepgram = DeepgramVoice()
                api_key = deepgram.get_current_api_key()
                
                if not api_key:
                    st.error("❌ DeepgramVoice could not get API key")
                elif api_key == "your_deepgram_api_key_here":
                    st.error("❌ DeepgramVoice got placeholder API key")
                else:
                    st.success(f"✅ DeepgramVoice has valid API key: {api_key[:8]}...{api_key[-4:]}")
                    
                    # Test actual API call
                    st.info("🌐 Testing API endpoint...")
                    import requests
                    
                    headers = {"Authorization": f"Token {api_key}"}
                    response = requests.get("https://api.deepgram.com/v1/projects", headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        st.success("✅ Deepgram API connection successful!")
                    else:
                        st.error(f"❌ Deepgram API error: {response.status_code} - {response.text}")
                        
            except Exception as e:
                st.error(f"💥 Deepgram test error: {e}")
    
    # File System Debug
    with st.expander("📁 File System Debug"):
        st.markdown("**Checking file system:**")
        
        # Check if secrets.toml exists (shouldn't in cloud)
        secrets_local = ".streamlit/secrets.toml"
        if os.path.exists(secrets_local):
            st.warning(f"⚠️ Local secrets.toml exists: {secrets_local}")
            try:
                with open(secrets_local, 'r') as f:
                    content = f.read()
                    st.code(content[:200] + "..." if len(content) > 200 else content)
            except:
                st.error("Cannot read local secrets.toml")
        else:
            st.info("ℹ️ No local secrets.toml (expected for cloud)")
        
        # Check utils directory
        if os.path.exists("utils"):
            st.success("✅ utils directory exists")
            utils_files = os.listdir("utils")
            st.code(f"Files: {utils_files}")
        else:
            st.error("❌ utils directory missing")
    
    # Summary and Next Steps
    st.markdown("---")
    st.subheader("📋 Summary & Next Steps")
    
    st.info("""
    **If you see errors above:**
    
    1. **API Key Issues:** Make sure your Streamlit Cloud secrets are configured exactly as:
    ```
    [api_keys]
    deepgram = "53e5bd9532e7084b6d0f49373cff9f7195e155b7"
    speechify = "W1vp8RVy2tnAw0GEj0NPqRszlWIXCfiDyLR5qOsY1rw="
    ```
    
    2. **Deployment Issues:** Check your Streamlit Cloud logs for deployment errors
    
    3. **Code Issues:** Make sure the latest code is deployed (check commit hash)
    
    4. **Cache Issues:** Try restarting your Streamlit Cloud app
    """)

if __name__ == "__main__":
    debug_environment()