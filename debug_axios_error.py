#!/usr/bin/env python3
"""
Debug AxiosError in Mixbot
This script helps identify potential causes of AxiosError
"""
import streamlit as st
import requests
import json
import time
from datetime import datetime

def test_network_connectivity():
    """Test various network endpoints that might cause AxiosError"""
    
    st.title("🔍 AxiosError Debug Tool")
    st.markdown("This tool helps identify potential network issues that might cause AxiosError")
    
    # Test endpoints
    test_urls = [
        "https://share.streamlit.io",
        "https://api.streamlit.io",
        "https://www.google.com",
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/500",
        "https://httpbin.org/delay/3"
    ]
    
    st.subheader("🌐 Network Connectivity Tests")
    
    results = []
    
    for url in test_urls:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{url}**")
        
        with col2:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    st.success(f"✅ {response.status_code}")
                else:
                    st.warning(f"⚠️ {response.status_code}")
                
                results.append({
                    "url": url,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "success": True
                })
                
            except requests.exceptions.Timeout:
                st.error("⏰ Timeout")
                results.append({
                    "url": url,
                    "status_code": None,
                    "response_time": None,
                    "success": False,
                    "error": "Timeout"
                })
            except requests.exceptions.ConnectionError:
                st.error("🔌 Connection Error")
                results.append({
                    "url": url,
                    "status_code": None,
                    "response_time": None,
                    "success": False,
                    "error": "Connection Error"
                })
            except Exception as e:
                st.error(f"❌ {type(e).__name__}")
                results.append({
                    "url": url,
                    "status_code": None,
                    "response_time": None,
                    "success": False,
                    "error": str(e)
                })
        
        with col3:
            if results and results[-1]["success"]:
                st.write(f"{results[-1]['response_time']:.2f}s")
            else:
                st.write("N/A")
    
    # Summary
    st.subheader("📊 Test Summary")
    
    successful_tests = sum(1 for r in results if r["success"])
    total_tests = len(results)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Successful Tests", successful_tests)
    
    with col2:
        st.metric("Failed Tests", total_tests - successful_tests)
    
    with col3:
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Potential AxiosError causes
    st.subheader("🔍 Potential AxiosError Causes")
    
    if successful_tests < total_tests:
        st.warning("**Network Issues Detected:**")
        st.markdown("""
        - **Connection Problems**: Some endpoints are unreachable
        - **Timeout Issues**: Slow network responses
        - **DNS Issues**: Domain resolution problems
        - **Firewall/Proxy**: Network restrictions
        
        **These could cause AxiosError in your app!**
        """)
    else:
        st.success("**Network connectivity looks good!**")
        st.markdown("""
        If users are still getting AxiosError, it might be:
        - **Browser-specific issues**
        - **Streamlit Cloud deployment problems**
        - **User's network environment**
        - **CORS issues**
        """)
    
    # Browser compatibility check
    st.subheader("🌐 Browser Compatibility")
    
    st.markdown("""
    **AxiosError is typically a JavaScript error. Common causes:**
    
    1. **CORS Issues**: Cross-origin requests blocked
    2. **Network Timeouts**: Slow connections
    3. **SSL/TLS Issues**: Certificate problems
    4. **Browser Extensions**: Ad blockers, security extensions
    5. **Streamlit Cloud Issues**: Platform-specific problems
    
    **To debug further:**
    - Ask users to check browser console (F12)
    - Try different browsers
    - Check if it happens on mobile vs desktop
    - Verify if it's specific to certain file types/sizes
    """)
    
    # Recommendations
    st.subheader("🛠️ Recommendations")
    
    st.markdown("""
    **Immediate Actions:**
    1. **Add better error handling** in your app
    2. **Implement retry logic** for failed requests
    3. **Add user-friendly error messages**
    4. **Log detailed error information**
    
    **Long-term Solutions:**
    1. **Monitor error patterns** using your error dashboard
    2. **Implement fallback mechanisms**
    3. **Add network status indicators**
    4. **Consider CDN for better global performance**
    """)
    
    # Export results
    if st.button("📥 Export Test Results"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"network_test_results_{timestamp}.json"
        
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "test_results": results,
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate
            }
        }
        
        st.download_button(
            label="Download Results",
            data=json.dumps(export_data, indent=2),
            file_name=filename,
            mime="application/json"
        )

if __name__ == "__main__":
    test_network_connectivity() 