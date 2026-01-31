import matplotlib.pyplot as plt
import chess.svg
import base64
import io

def generate_chart_html(evals):
    """Génère le graphique d'évaluation en HTML/Base64."""
    # Design "Dark Mode" pour coller à l'UI
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 3))
    
    # On trace la ligne
    ax.plot(evals, color='#2196F3', linewidth=3, antialiased=True)
    
    # On remplit sous la courbe pour le style "Area Chart"
    ax.fill_between(range(len(evals)), evals, color='#2196F3', alpha=0.1)
    
    # Ligne d'équilibre au centre (0.0)
    ax.axhline(0, color='white', linewidth=0.5, alpha=0.5)
    
    # Nettoyage des bordures
    ax.axis('off')
    
    # Conversion en image pour le Web
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=100)
    plt.close(fig)
    
    b64 = base64.b64encode(buf.getvalue()).decode()
    
    return f"""
    <div style="text-align:center; background:#1e1e1e; border-radius:10px; padding:15px; border:1px solid #333; margin:20px 0;">
        <p style="color:#aaa; font-size:0.7rem; margin-bottom:10px; letter-spacing:1px;">COURBE DE TENSION (EVALS)</p>
        <img src="data:image/png;base64,{b64}" style="width:100%;" />
    </div>
    """

def generate_svg_board(game_obj, move_number, orientation_white=True):
    """Génère le plateau SVG à un coup précis."""
    board = game_obj.board()
    moves = list(game_obj.mainline_moves())
    
    for i in range(min(move_number, len(moves))):
        board.push(moves[i])
    
    side = chess.WHITE if orientation_white else chess.BLACK
    
    svg_data = chess.svg.board(
        board, 
        orientation=side, 
        size=350,
        style="""
            .square.light { fill: #eae9d2; }
            .square.dark { fill: #4b7399; }
        """
    )
    
    b64 = base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
    
    return f"""
    <div style="text-align:center; margin:25px 0;">
        <img src="data:image/svg+xml;base64,{b64}" style="border:5px solid #333; border-radius:5px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);" width="300" />
        <p style="color:#666; font-size:0.8rem; margin-top:8px;">Position après le coup {move_number}</p>
    </div>
    """