"""
このファイルは、画面表示に特化した関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import streamlit as st
import utils
import constants as ct


############################################################
# 関数定義
############################################################

def display_app_title():
    """
    タイトル表示
    """
    st.markdown(f"## {ct.APP_NAME}")


def display_initial_ai_message():
    """
    AIメッセージの初期表示
    """
    # 会話ログがまだない場合（＝最初の表示時）のみ実行
    if not st.session_state.get("messages"):
        with st.chat_message("assistant"):
            st.markdown("こんにちは。私は社内文書の情報をもとに回答する生成AIチャットボットです。左のサイドバーで利用目的を選択し、画面下部のチャット欄からメッセージを送信してください。")


def display_conversation_log():
    """
    会話ログの一覧表示
    """
    # 会話ログのループ処理
    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                # ログに保存された整形済みデータを表示する
                content_data = message["content"]
                if content_data["mode"] == ct.ANSWER_MODE_1:
                    render_search_response(content_data)
                else:
                    render_inquiry_response(content_data)


def display_search_llm_response(llm_response):
    """
    「社内文書検索」モードにおけるLLMレスポンスを解析・表示し、ログ用データを返す
    """
    log_content = {"mode": ct.ANSWER_MODE_1}

    if llm_response["context"] and llm_response["answer"] != ct.NO_DOC_MATCH_ANSWER:
        main_doc = llm_response["context"][0]
        sub_docs = llm_response["context"][1:]

        # ログ用データを作成
        log_content["main_message"] = "入力内容に関する情報は、以下のファイルに含まれている可能性があります。"
        log_content["main_file_path"] = main_doc.metadata["source"]
        if "page" in main_doc.metadata:
            log_content["main_page_number"] = main_doc.metadata["page"]

        sub_choices = []
        seen_sources = {log_content["main_file_path"]}
        for doc in sub_docs:
            source = doc.metadata["source"]
            if source not in seen_sources:
                seen_sources.add(source)
                choice = {"source": source}
                if "page" in doc.metadata:
                    choice["page_number"] = doc.metadata["page"]
                sub_choices.append(choice)
        
        if sub_choices:
            log_content["sub_message"] = "その他、ファイルありかの候補を提示します。"
            log_content["sub_choices"] = sub_choices
        
        # 作成したデータをレンダリング関数に渡して表示
        render_search_response(log_content)

    else:
        log_content["answer"] = ct.NO_DOC_MATCH_MESSAGE
        log_content["no_file_path_flg"] = True
        st.warning(ct.NO_DOC_MATCH_MESSAGE, icon=ct.WARNING_ICON)

    return log_content


def display_contact_llm_response(llm_response):
    """
    「社内問い合わせ」モードにおけるLLMレスポンスを解析・表示し、ログ用データを返す
    """
    log_content = {"mode": ct.ANSWER_MODE_2, "answer": llm_response["answer"]}
    
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        unique_sources = {}
        for doc in llm_response["context"]:
            source = doc.metadata["source"]
            if source not in unique_sources:
                unique_sources[source] = doc.metadata.get("page")

        file_info_list = []
        for source, page in unique_sources.items():
            file_info = {"source": source}
            if page is not None:
                file_info["page_number"] = page
            file_info_list.append(file_info)

        log_content["message"] = "情報源"
        log_content["file_info_list"] = file_info_list

    # 作成したデータをレンダリング関数に渡して表示
    render_inquiry_response(log_content)
    return log_content


def render_search_response(content_data):
    """
    「社内文書検索」モードの整形済みデータを画面にレンダリングする
    """
    if content_data.get("no_file_path_flg"):
        st.warning(content_data["answer"], icon=ct.WARNING_ICON)
        return

    st.markdown(content_data["main_message"])
    icon = utils.get_source_icon(content_data['main_file_path'])
    
    # ------------------------------------------------------------
    # 【問題4】の回答箇所 1
    # ------------------------------------------------------------
    main_display_text = content_data['main_file_path']
    if main_display_text.endswith(".pdf") and "main_page_number" in content_data:
        main_display_text += f" (ページNo.{content_data['main_page_number'] + 1})"
    st.success(main_display_text, icon=icon)
    # ------------------------------------------------------------
    
    if "sub_message" in content_data:
        st.markdown(content_data["sub_message"])
        for sub_choice in content_data["sub_choices"]:
            icon = utils.get_source_icon(sub_choice['source'])
            # ------------------------------------------------------------
            # 【問題4】の回答箇所 2
            # ------------------------------------------------------------
            sub_display_text = sub_choice['source']
            if sub_display_text.endswith(".pdf") and "page_number" in sub_choice:
                sub_display_text += f" (ページNo.{sub_choice['page_number'] + 1})"
            st.info(sub_display_text, icon=icon)
            # ------------------------------------------------------------

def render_inquiry_response(content_data):
    """
    「社内問い合わせ」モードの整形済みデータを画面にレンダリングする
    """
    st.markdown(content_data["answer"])
    if "file_info_list" in content_data:
        st.divider()
        st.markdown(f"##### {content_data['message']}")
        for file_info in content_data["file_info_list"]:
            icon = utils.get_source_icon(file_info["source"])
            # ------------------------------------------------------------
            # 【問題4】の回答箇所 3
            # ------------------------------------------------------------
            display_text = file_info["source"]
            if display_text.endswith(".pdf") and "page_number" in file_info:
                display_text += f" (ページNo.{file_info['page_number'] + 1})"
            st.info(display_text, icon=icon)
            # ------------------------------------------------------------