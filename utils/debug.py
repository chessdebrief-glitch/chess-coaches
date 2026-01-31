import time
import functools
import streamlit as st

def pipeline_trace(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 1. Capturer l'entrée
        start_time = time.perf_counter()
        func_name = func.__name__
        
        # 2. Exécuter la fonction
        try:
            result = func(*args, **kwargs)
            status = "SUCCESS"
        except Exception as e:
            result = str(e)
            status = "ERROR"
            raise e
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            # 3. Stocker dans le State de Streamlit pour l'UI de debug
            if "traces" not in st.session_state:
                st.session_state.traces = []
                
            st.session_state.traces.append({
                "timestamp": time.strftime("%H:%M:%S"),
                "function": func_name,
                "args": args[0] if args else kwargs, # On simplifie l'input
                "output": result,
                "duration": f"{duration:.3f}s",
                "status": status
            })
        return result
    return wrapper
