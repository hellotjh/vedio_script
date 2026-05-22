from dask.array.slicing import expander
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
import re
import requests
import streamlit as st
def search_wikipedia(query):
    try:
        response = requests.get(
            "https://zh.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": 3,
                "format": "json",
            },
            headers={"User-Agent": "langchain-demo/1.0"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("维基百科搜索失败，跳过参考资料：", e)
        return ""

    results = data.get("query", {}).get("search", [])
    summaries = []
    for item in results:
        title = item.get("title", "")
        snippet = re.sub(r"<.*?>", "", item.get("snippet", ""))
        summaries.append(f"{title}: {snippet}")
    return "\n".join(summaries)

with st.sidebar:
    key=st.text_input("请输入OpenAI API密钥",type="password")
    st.markdown("[获取OpenAI API密钥](https://xcode.best/console/token)")

st.title(" ▶ 视频脚本生成器")
subject1=st.text_input("请输入视频的主题")
time1=st.number_input("请输入视频的大致时长（单位：分钟）")
creativity1=st.slider("请输入视频脚本的创造力（数字小说明更严谨，数字大说明更多样）",min_value=0.0,max_value=1.0,value=0.5,step=0.01)
button1=st.button("生成脚本")

def generate_script(subject,video_length,creativity,api_key):
    title_template=ChatPromptTemplate.from_messages([
        ("human","请为{subject}这个主题的视频想一个吸引人的标题，只需输出一个标题")
    ])
    script_template=ChatPromptTemplate.from_messages([("human","""你是一位短视频频道的博主。
    根据以下标题和相关信息，为短视频频道视频标题：{title}，视频时长：{duration}分钟，生成的脚本的长度
    要求抓住眼球，中间提供干货内容，结尾有惊喜，脚本格式也请按照整体内容的表达方式要尽量轻松有趣，吸引年轻
    人,语言为中文简体。脚本内容可以结合以下维基百科搜索出的信息，但仅作为参考，只结合相关的进行忽略
    ：'''{wikipedia_search}'''""")])
    model = ChatOpenAI(model="gpt-5.5",
                       api_key=api_key,
                       base_url="https://xcode.best/v1", temperature=creativity,
                       max_tokens=30000,streaming=True)
    title_chain=title_template|model
    script_chain=script_template|model
    title=title_chain.invoke({"subject":subject}).content
    search_result=search_wikipedia(subject)
    script=script_chain.invoke({"title":title,"duration":video_length,
                         "wikipedia_search":search_result}).content
    return search_result,title,script
if button1 and not subject1:
    st.info("请输入视频的主题！")
    st.stop()
elif button1 and not time1:
    st.info("请输入视频的大致时长（单位：分钟）！")
    st.stop()
elif button1 and  time1<0.1:
    st.info("视频时长过短！")
    st.stop()
elif button1 and not key:
    st.info("请输入OpenAI API密钥!")
    st.stop()
elif button1:
    with st.spinner("AI正在思考中，请稍后..."):
        search_result,title,script=generate_script(subject1,time1,creativity1,key)
    st.success("视频脚本已生成！")
    st.subheader("标题：")
    st.write(title)
    st.subheader("视频脚本：")
    st.write(script)
    # with expander("维基百科搜索结果"):
    #     st.info(search_result)
