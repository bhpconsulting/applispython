"""
Calculette
"""

def run():
    import streamlit as st

    # Titre de l'application
    st.title("Calculette")

    # Initialisation de la session pour enregistrer les entrées et l'opération (par exemple 5*3)
    if "calcul" not in st.session_state:
        st.session_state.calcul = ""
        
    #---------------------------------
    # Fonction pour mettre à jour la session avec les boutons
    def maj_calcul(value):
        st.session_state.calcul += str(value)
        
    #---------------------------------------- 
    # Fonction pour effacer l'entrée
    def effacer():
        st.session_state.calcul = ""
        
    #------------------------------------
    # Fonction pour calculer le résultat
    def calculer():
        try:
            st.session_state.calcul = str(eval(st.session_state.calcul))
        except:
            st.session_state.calcul = "Erreur"
            
    #--------------------------------------
    
    # Affichage de l'entrée actuelle
    st.text_input("Entrée", value=st.session_state.calcul, key="display")

    # Disposition des boutons de la calculatrice
    col1, col2, col3, col4 = st.columns(4)

    # utilisation de caractères Emoij pour affichage sur le bouton
    with col1:
        st.button("7️⃣", on_click=maj_calcul, args=("7",))
        st.button("4️⃣", on_click=maj_calcul, args=("4",))
        st.button("1️⃣", on_click=maj_calcul, args=("1",))
        st.button("0️⃣", on_click=maj_calcul, args=("0",))

    with col2:
        st.button("8️⃣", on_click=maj_calcul, args=("8",))
        st.button("5️⃣", on_click=maj_calcul, args=("5",))
        st.button("2️⃣", on_click=maj_calcul, args=("2",))
        st.button("🔸", on_click=maj_calcul, args=(".",))

    with col3:
        st.button("9️⃣", on_click=maj_calcul, args=("9",))
        st.button("6️⃣", on_click=maj_calcul, args=("6",))
        st.button("3️⃣", on_click=maj_calcul, args=("3",))
        st.button("🟰", on_click=calculer)

    with col4:
        st.button("➗", on_click=maj_calcul, args=(" / ",))
        st.button("✖️", on_click=maj_calcul, args=(" * ",))
        st.button("➖", on_click=maj_calcul, args=(" - ",))
        st.button("➕", on_click=maj_calcul, args=(" + ",))
        st.button("🆑", on_click=effacer)
        
    # Relance du portail            
    url = "https://courspython.org"
    st.markdown(f"<a href={url} target='_self'>Cliquez ici pour relancer le portail</a>", unsafe_allow_html=True)

# Si l'application est lancée directement (en dehors du portail), lancer l'application
if __name__ == "__main__":
    run()  
