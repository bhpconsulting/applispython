# -*- coding: utf-8 -*-
"""
Recherche de fichiers PDF sur mots-clés 
Recherche approximative s'affranchissant des accents et de la casse
"""
def run():
    import re # pour gérer les 'expressions régulières'
    import streamlit as st # pour affichage web
    import requests # pour afficher un fichier par son url
    from io import BytesIO # pour manipuler des flux de données binaires
    import fitz # alias de PyMuPDF, pour manipuler des fichiers pdf 
    from concurrent.futures import ThreadPoolExecutor  # pour exécuter des tâches en parallèle
    import os # pour gérer les répertoires de fichiers
    from fuzzysearch import find_near_matches  # recherche approximative
    import unicodedata # pour normaliser le texte des pdf et les mots-clés (accents, casse)
    
    # ------------------------------
    def cartouche():
        # explications en tête dans une seule chaîne HTML
        html_content = """
        <p style='color: blue; margin-bottom: 0px;font-size: 20px;'>Saisir les mots-clés, séparés par des virgules,</p>
        <p style='color: blue; margin-bottom: 0px;font-size: 20px;'>puis cliquer sur 'Afficher résultat recherche'.</p>
        <p style='color: red; margin-bottom: 0px;font-size: 20px; font-style: italic;'>Les mots-clés sont insensibles aux accents et à la casse.</p>
        <br>
        """
        # affichage de tout le contenu HTML dans un seul appel de st.markdown
        st.markdown(html_content, unsafe_allow_html=True)
        
    #-----------------------------------------------
    def sup_rep(rep):
        # supprimer les fichiers du répertoire 'rep'
        if os.path.exists(rep):
            for fichier in os.listdir(rep):
                chemin_fichier = os.path.join(rep, fichier)
                if os.path.isfile(chemin_fichier):
                    os.remove(chemin_fichier)  # supprime uniquement les fichiers
        else:
            st.write(f"Le répertoire {rep} n'existe pas") 
    
    #-------------------------------
    def normaliser_texte(texte):
        # transformation des caractères accentués en leur équivalent sans accent
        texte = unicodedata.normalize('NFD', texte)
        texte = ''.join(c for c in texte if unicodedata.category(c) != 'Mn')
        # conversion en minuscules
        texte = texte.lower() 
        return texte
                    
    #--------------------------------------------------
    def surligner_mots_cles(pdf_file, mots_cles_positions, output_fich):
        # pour mettre en surbrillance les 'keywords' trouvés dans le fichier 'pdf_file'l'
        # 'mots_cles_poitions' est le dictionnaire associé au fichier 'pdf_file' ayant comme clé l'indice de la page du fichier, 
        # et comme valeur la liste des 2 positions de départ et de fin d'un des mot-clés trouvés
        # 'output_fich' est l'adresse du fichier 
        with fitz.open(stream=pdf_file, filetype="pdf") as doc: 
            for page_num, positions in mots_cles_positions.items():  # boucle sur les pages de 'doc'
                page = doc[page_num]  # indice de la page
                for (start, end) in positions:
                    try:
                        # extraction du texte correspondant
                        text_segment = page.get_text()[start:end]

                        # recherche dans la page
                        rects = page.search_for(text_segment)
                        if rects:
                            for rect in rects:
                                page.add_highlight_annot(rect) # mise en surbrillance du segment de texte
                        else:
                            st.write(f"Aucune correspondance exacte pour '{text_segment}' à la page {page_num}.")
                    except Exception as e:
                        st.write(f"Erreur surlignage pour '{text_segment}' à la page {page_num} : {e}")

            # sauvegarde le fichier PDF avec les surlignages
            doc.save(output_fich)
    
    #--------------------------------
    def tri_result(results):
        # tri de 'results' par ordre décroissant d'occurrence des mots-clés 
        results_new = []
        for result in results:
            nb_occur = 0 # nombre d'occurrences d'un ou des mots-clé(s) dans le fichier
            for keyword, positions in result['matches'].items():
                # positions est une liste de tuples. Un tuple = (start,end) du mot-clé
                nb_occur += len(positions)
            # s'il y a au moins une occurrence on crée un élément (dictionnaire) dans la liste 'results_new'  
            # en rajoutant un élément du dictionnaire (nb_occur)
            if nb_occur != 0: 
                url = result['url']
                matches = result['matches']
                nom = result['nom']
                results_new.append({"url": url, "matches": matches,"nom": nom,"nb_occur": nb_occur}) 
        # la liste results_sorted est trié sur la clé 'nb_occur'
        results_sorted = sorted(results_new, key=lambda x: x["nb_occur"], reverse = True)
        return results_sorted   
     
    #--------------------------------
    def manip_url_gdrive(fichier):
        # transformation du lien G-Drive du fichier PDF en une url que 'requests' peut traiter
        # utilisé que dans le cas où les newsletters sont stockées sur G-Drive
        resultat = fichier.rsplit("/", 1)[0]  # récupère tout avant le dernier '/' (on enlève 'view?asp=sharing')
        id = resultat.rsplit("/", 1)[1]  # récupère tout après le dernier '/' (c'est à dire l'id)
        resultat = "https://drive.google.com/uc?export=download&id=" + id
        return resultat
            
    # --------------------------------
    def fichiers(noms_fich):
        # affichage des newsletters examinées
        st.markdown("<h4 style='color: blue;'>Newsletters examinées : </h4>", unsafe_allow_html=True) 
        chaine = ', '.join(noms_fich) # transformation de la liste en une chaîne d'éléments séparés par une virgule
        st.markdown(f"<h5 style='color: black;'>{chaine}</h5>", unsafe_allow_html=True)   
    
    # --------------------------------
    def extract_text_fitz(pdf_file):
        # lit le fichier PDF et extrait le texte avec PyMuPDF
        with fitz.open(stream=pdf_file, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
        return text
    
    #---------------------------------------
    def recherche_keywords(text,keywords):
        # recherche des 'keywords' dans 'text''
        results = {}
        for keyword in keywords:
            # m.start() est la position de départ de 'keyword' dans 'text'
            matches = [m.start() for m in re.finditer(keyword, text, re.IGNORECASE)]
            results[keyword]= matches
            
        return results
    
    #---------------------------------------
    def recherche_keywords_approximatif(text, keywords, max_dist):
        # recherche des mots-clés avec tolérance aux erreurs de frappe (principe 'distance de Levenshtein')
        # supprime les accents du texte et des mots-clés
        text_normalise = normaliser_texte(text)
        keywords_normalises = [normaliser_texte(keyword) for keyword in keywords]

        results = {}
        for original, normalise in zip(keywords, keywords_normalises):
            matches = find_near_matches(normalise, text_normalise, max_l_dist=max_dist)
            # m.start est la position de départ de 'keyword' dans 'text', m.end la position de fin
            results[original] = [(m.start, m.end) for m in matches]
        return results
    
    #----------------------------------
    def process_file(nom, url, choix, keywords,output_path,max_dist):
        # extraction du texte du fichier'nom' accessible par son 'url' et recherche des 'keywords'
        # surlignage dans le PDF s'il y a des mots-clés trouvés dans le fichier
        try:
            if choix == "gdrive":
                url_modif = manip_url_gdrive(url)
            else:
                url_modif = url
                
            response = requests.get(url_modif)  # téléchargement du fichier
            response.raise_for_status()

            with BytesIO(response.content) as pdf_file:
                # extraction du texte
                text = extract_text_fitz(pdf_file)
                
                # recherche approximative des mots-clés
                keyword_matches = recherche_keywords_approximatif(text, keywords, max_dist)
                                 
                # association des positions trouvées avec les numéros de pages
                # 'keyword_matches' = dictionnaire avec comme clé l'indice de la page du fichier, 
                # et comme valeur la liste des 2 positions de départ et de fin d'un des mot-clés trouvés
                mots_cles_positions = {}
                with fitz.open(stream=pdf_file, filetype="pdf") as doc:
                    for page_num, page in enumerate(doc): # boucle sur les pages du fichier pdf
                        page_text = page.get_text()  # extraction du texte de la page
                        mots_cles_positions[page_num] = [
                            (m.start, m.end) for keyword in keywords 
                            for m in find_near_matches(normaliser_texte(keyword), normaliser_texte(page_text), max_l_dist=max_dist)
                        ]
                
                # test mots-clés trouvés        
                succes = False  # succes = True s'il y a au moins un mot-clé trouvé
                for page_num, positions in mots_cles_positions.items():
                    if positions != []: 
                        succes = True
                        break
           
                if succes: # on ne surligne que s'il y a au moins un mot-clé trouvé
                    # surlignage des mots-clés 
                    output_fich = output_path + nom + ".pdf"
                    surligner_mots_cles(response.content, mots_cles_positions, output_fich)                
     
                return {"url": url, "matches": keyword_matches, "nom": nom}

        except requests.RequestException as e:
            return {"error": f"Erreur téléchargement {url}: {e}"}
        except Exception as e:
            return {"error": f"Erreur lecture/surlignage PDF {url}: {e}"}
    
    #--------------------------------------
    def recherche_in_pdfs(fichiers_nwl, keywords, choix, output_path, max_dist):
        # recherche des mots-clés dans des fichiers PDF accessibles via leurs URLs
        # permet de paralléliser les tâches, ici, chaque fichier PDF est traité dans un thread distinct.
        # cela optimise la performance
        results = []
        with ThreadPoolExecutor() as executor:
            futures = []
            for nom, url in fichiers_nwl.items(): # nom et url d'ne newsletter
                futures.append(executor.submit(process_file, nom, url, choix, keywords,output_path,max_dist))
            for future in futures:
                results.append(future.result())

        return results

    #------------------------------------
    st.markdown("<h2 style='color: black;'>Recherche de Newsletters sur mots-clés</h2>", unsafe_allow_html=True) 
    
    # dictionnaire des url des newsletters
    fichiers_nwl = {

          "NWL90":"https://www.agirabcd.fr/NEWSLETTER/N90/N90_NWL.pdf",        
          "NWL89":"https://www.agirabcd.fr/NEWSLETTER/N89/NWL89.pdf", 
          "NWL88":"https://www.agirabcd.fr/NEWSLETTER/N88/N88-1.pdf", 
          "NWL87":"https://www.agirabcd.fr/NEWSLETTER/N87/NWL_87.pdf", 
          "NWL86":"https://www.agirabcd.fr/NEWSLETTER/N86/N86_NWL.pdf", 
          "NWL85":"https://www.agirabcd.fr/NEWSLETTER/N85/N85_NWL.pdf", 
          "NWL84":"https://www.agirabcd.fr/NEWSLETTER/N84/N84_NWL.pdf", 
          "NWL83":"https://www.agirabcd.fr/NEWSLETTER/N83/83-NWL.pdf", 
          "NWL82":"https://www.agirabcd.fr/NEWSLETTER/N82/82-NWL.pdf", 
          "NWL81":"https://www.agirabcd.fr/NEWSLETTER/N81/81_NWL.pdf", 
          "NWL80":"https://www.agirabcd.fr/NEWSLETTER/N80/80_NWL.pdf"
        
    }
    # chez Alwaysdata, chemin d'accès au fichier provisoire créé lors de la mise en surbrillance
    rep = "/home/sitebj/www/prov"
    chemin = rep + "/pdf_surligne_"  
    
    # chemin de l'URL d'accès au fichier provisoire pdf mis en surbrillance (output_path)
    # pour ouverture sur clic
    racine = "https://sitebj.alwaysdata.net/prov/pdf_surligne_"
    
    # suppression des fichiers du répertoire 'rep'
    sup_rep(rep)
        
    # choix de l'emplacement des fichiers des newsletters ('normal' ou 'gdrive')
    # 'gdrive' dans le cas où les fichiers auraient été copiés dur G-Drive, 
    # 'normal' sinon quand ils sont sur leur emplacement d'origine sur le site AGIRabcd
    choix = "normal"
    
    # affichage de la liste des newsletters examinées
    fichiers(list(fichiers_nwl.keys()))
    
    cartouche()  # texte explicatif
  
    # max_dist = tolérance aux erreurs de frappe (0 si correspondance exacte)
    max_dist = st.radio(
      "Correspondance exacte ?",
      options=["Oui", "Non (mot-clé approximatif - nom d'une personne par exemple)"],
      horizontal=True      )
    if max_dist == "Oui":
        max_dist = 0
    else:
        max_dist = 1
    
    keywords = st.text_input("Mots-clés")
    keywords = keywords.split(',')  # transformation de la chaîne en liste
    # on supprime les 'blancs' de la liste des mots-clés (utile si rien n'a été saisi)
    while "" in keywords:
        keywords.remove("")
        
    if st.button("Afficher résultat recherche") :
        # à chaque fichier du répertoire correspond un élément de la liste 'results'
        # sous forme d'un dictionnaire constitué du nom du fichier (associé à la clé 'url')
        # et d'un sous-dictionnaire (associé à la clé 'matches') constitué des mots-clés successifs
        # et de la liste des positions de départ et de fin du mot-clé considéré
        
        results = recherche_in_pdfs(fichiers_nwl, keywords, choix, chemin, max_dist) # lancement de la recherche
        
        # tri de 'results' par ordre d'occurrence des mots-clés décroissant
        results_sorted = tri_result(results)
        
        if len(results_sorted) != 0:
            for result in results_sorted:
                # result['matches'] est le dictionnaire constitué d'une clé (keyword) et d'une liste des positions (départ et fin) de keyword
                # result['matches'].items() déstructure en 'keyword' et 'positions'
                # len(positions) = nombre d'éléments de la liste donc le nombre d'occurrences de keyword
       
                nwl = result['nom']  # son nom
                url_surlign = racine + nwl +".pdf" # url du fichier PDF surligné
                #-----------------------
                
                st.markdown(f"<h4 style='color: blue;'>Dans la Newsletter <a href= '{url_surlign}' target='_blank'>{nwl}</a></h4>",unsafe_allow_html=True)
                for keyword, positions in result['matches'].items(): 
                    if len(positions) != 0:
                        st.markdown(f"<h4 style='color: orange;'>--- le mot-clé '{keyword}' a été trouvé {len(positions)} fois </h4>", unsafe_allow_html=True)
        
        else:
            st.markdown("<h4 style='color: red;'>aucun mot-clé trouvé dans les newsletters examinées (ou aucun mot-clé saisi)</h4>", unsafe_allow_html=True)
    
# Si l'application est lancée directement (en dehors du portail), lancer l'application
if __name__ == "__main__":    
    run()