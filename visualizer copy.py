import matplotlib.pyplot as plt
import chess.svg
import base64
import io

def generate_chart_html(evals):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(evals, color='#2196F3', linewidth=3)
    ax.fill_between(range(len(evals)), evals, color='#2196F3', alpha=0.1)
    ax.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f'<div class="chart-container"><img src="data:image/png;base64,{b64}" width="100%"/></div>'

def generate_svg_board(board, orientation):
    svg_data = chess.svg.board(board, orientation=orientation, size=350)
    b64 = base64.b64encode(svg_data.encode()).decode()
    return f'<div class="diag-container"><img src="data:image/svg+xml;base64,{b64}" width="300"/></div>'