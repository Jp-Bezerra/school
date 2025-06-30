import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from pyvis.network import Network
import tempfile
import os

# Carregar dados
G = nx.read_gexf("dados/data_school.gexf")
meta = pd.read_csv("dados/metadata.txt", sep="\t", header=None, names=["id","turma","sexo"])
meta["id"] = meta["id"].astype(str)

atributos = meta.set_index("id")[["turma","sexo"]].to_dict(orient="index")
for node in G.nodes:
    if node in atributos:
        G.nodes[node]["turma"] = atributos[node]["turma"]
        G.nodes[node]["sexo"] = atributos[node]["sexo"]
    else:
        G.nodes[node]["turma"] = "Desconhecida"
        G.nodes[node]["sexo"] = "Desconhecido"

# Visualização
st.title("Interações escolares")


st.sidebar.title('Filtro por Turma')
turma_selecionada = st.sidebar.selectbox('Escolha a turma:', ('Todas', '1A','1B', '2A', '2B', '3A', '3B', '4A', '4B', '5A', '5B'))

if turma_selecionada != "Todas":
    nos_filtrados = [n for n, d in G.nodes(data=True) if d.get("turma") == turma_selecionada]
    G = G.subgraph(nos_filtrados).copy()

st.markdown(f"**Número de nós:** {G.number_of_nodes()}")
st.markdown(f"**Número de arestas:** {G.number_of_edges()}")

st.subheader("Visualização de Rede")

net = Network(height="600px", width="100%", notebook=False, directed=False)
net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=100, spring_strength=0.001, damping=0.09)

for node, data in G.nodes(data=True):
    cor = "#FFC0CB" if data.get("sexo") == "F" else "#87CEFA" if data.get("sexo") == "M" else "#D3D3D3"
    net.add_node(
        node,
        label=node,
        title=f"Turma: {data.get('turma', 'Desconhecida')} Sexo: {data.get('sexo', 'Desconhecido')}",
        color=cor
    )

net.toggle_physics(True)
net.show_buttons(filter_=['physics'])

for source, target in G.edges():
    net.add_edge(source, target)

st.subheader("📊 Métricas Estruturais da Rede")

# Densidade (esparsidade = 1 - densidade)
densidade = nx.density(G)
st.markdown(f"**Densidade:** {densidade:.4f}")

# Assortatividade (baseado em grau)
try:
    assort = nx.degree_assortativity_coefficient(G)
    st.markdown(f"**Assortatividade:** {assort:.4f}")
except:
    st.markdown("**Assortatividade:** não pôde ser calculada.")

# Clustering
if not nx.is_directed(G):
    clustering = nx.average_clustering(G)
    st.markdown(f"**Coeficiente de clustering global:** {clustering:.4f}")
else:
    clustering = nx.average_clustering(G.to_undirected())
    st.markdown(f"**Coeficiente de clustering global (convertido para não-dirigido):** {clustering:.4f}")

with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
    net.save_graph(tmp_file.name)
    html_path = tmp_file.name

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()
    st.components.v1.html(html, height=650, scrolling=True)    

st.subheader("Distribuição de Grau")

graus = [d for _, d in G.degree()]
fig, ax = plt.subplots()
ax.hist(graus, bins=20, color='skyblue', edgecolor='black')
ax.set_title("Distribuição de Grau dos Nós")
ax.set_xlabel("Grau")
ax.set_ylabel("Número de Nós")
st.pyplot(fig)

st.subheader("Centralidade dos Nós")

opcao_centralidade = st.selectbox("Escolha a métrica de centralidade", [
    "Degree", "Closeness", "Betweenness", "Eigenvector"
])

top_k = st.slider("Quantos nós mostrar no ranking?", 5, 20, 10)

# Calcula a centralidade
centralidade = {}
try:
    if opcao_centralidade == "Degree":
        centralidade = nx.degree_centrality(G)
    elif opcao_centralidade == "Closeness":
        centralidade = nx.closeness_centrality(G)
    elif opcao_centralidade == "Betweenness":
        centralidade = nx.betweenness_centrality(G)
    elif opcao_centralidade == "Eigenvector":
        centralidade = nx.eigenvector_centrality(G)
except nx.NetworkXException as e:
    st.error(f"Erro ao calcular a centralidade: {e}")

if centralidade:
    ranking = sorted(centralidade.items(), key=lambda x: x[1], reverse=True)[:top_k]
    df_ranking = pd.DataFrame(ranking, columns=["Nó", "Valor da Centralidade"])
    st.dataframe(df_ranking)
