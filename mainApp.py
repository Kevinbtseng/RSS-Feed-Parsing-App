import json
import flet as ft
import feedparser
from urllib.parse import urlparse

def load_bookmarks(page):
    bookmarks_json = page.client_storage.get("bookmarks")
    if bookmarks_json:
        return json.loads(bookmarks_json)
    return {}

def save_bookmarks(bookmarks, page):
    page.client_storage.set("bookmarks", json.dumps(bookmarks))


def toggle_bookmark(e, guid, title, full_text, pub_date, source, page):
    bookmarks = load_bookmarks(page)
    if guid in bookmarks:
        del bookmarks[guid]
        e.control.icon = ft.Icons.BOOKMARK_BORDER
        e.control.icon_color = None
    else:
        bookmarks[guid] = {
            "title" : title,
            "full_text" : full_text,
            "pub_date" : pub_date,
            "source" : source,
            "guid" : guid
        }
        e.control.icon = ft.Icons.BOOKMARK
        e.control.icon_color = "blue"

    save_bookmarks(bookmarks, page)
    e.control.update()



def show_bookmarks(page, news_list):
    page.current_view = "bookmarks"
    news_list.controls.clear()

    bookmarks = load_bookmarks(page)

    if not bookmarks:
        news_list.controls.append(ft.Text("No Bookmarks yet", color = "gray"))
        news_list.update()
        return
    
    for guid, article in bookmarks.items():
        def article_closure(articlefull_text, articleTitle, articleUrl, pub_date, source):
            def open_article(e):
                global current_article_url, current_article_title, current_article_text, current_article_date, current_article_source
                current_article_url = articleUrl
                current_article_title = articleTitle
                current_article_text = articlefull_text
                current_article_date = pub_date
                current_article_source = source
                modal_title.value = articleTitle
                modal_content.value = articlefull_text
                if articleUrl in load_bookmarks(page):
                    bookmark_button.icon = ft.Icons.BOOKMARK
                else:
                    bookmark_button.icon = ft.Icons.BOOKMARK_BORDER
                if article_dialog not in page.overlay:
                    page.overlay.append(article_dialog)
                article_dialog.open = True
                page.update()   
            return open_article
        news_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(article["title"], weight=ft.FontWeight.BOLD, size=16, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.BOOKMARK,
                        icon_color="blue",
                        tooltip="Remove bookmark",
                        on_click=lambda e, guid=guid: toggle_bookmark(
                                e, guid, article["title"], article["full_text"], article["pub_date"], article["source"], page
                        ),
                        data=guid
                    )
                ]),
                ft.Text(article["full_text"], size=14, italic=True),
                ft.Text(f"{article['pub_date']} | {article['source']}", size=12, color="gray")
            ], spacing=5),
            padding=10,
            border_radius=10,
            border=ft.border.all(1, "gray"),
            margin=5,
            on_click=article_closure(article["full_text"], article["title"], guid, article["pub_date"], article["source"]),
            ink=True  
        )
        news_list.controls.append(news_card)
    
    news_list.update()


def fetch_feed(feed_url, news_list, page):
    news_list.controls.clear()
    
    try:
        parsed_feed = feedparser.parse(feed_url)
        if parsed_feed.bozo:
            news_list.controls.append(ft.Text(f"Failed to retrieve data from {feed_url}", color="red"))
            news_list.update()
            return

        source = urlparse(feed_url).netloc

        bookmarks = load_bookmarks(page)

        for entry in parsed_feed.entries:
            title = entry.get("title", "No Title")
            summary = entry.get("summary", "No Summary Available")
            pub_date = entry.get("published", "No Date")
            getText = entry.get("content", [{}])
            try: 
                full_text = getText[0].get("value") if getText[0].get("value").strip() else summary
            except:
                full_text = summary
            tags = entry.get("tags", [{}])
            list_of_tags = []
            article_guid = entry.get("guid", None)
            try:
                for tag in tags:
                    list_of_tags.append(tag.get("term", "No Tags"))
            except AttributeError:
                pass
            
            def article_closure(articlefull_text, articleTitle, articleUrl, pub_date, source):
                def open_article(e):
                    global current_article_url, current_article_title, current_article_text, current_article_date, current_article_source
                    current_article_url = articleUrl
                    current_article_title = articleTitle
                    current_article_text = articlefull_text
                    current_article_date = pub_date
                    current_article_source = source
                    modal_title.value = articleTitle
                    modal_content.value = articlefull_text
                    if articleUrl in load_bookmarks(page):
                        bookmark_button.icon = ft.Icons.BOOKMARK
                    else:
                        bookmark_button.icon = ft.Icons.BOOKMARK_BORDER
                    if article_dialog not in page.overlay:
                        page.overlay.append(article_dialog)
                    article_dialog.open = True
                    page.update()   
                return open_article

            is_bookmarked = article_guid in bookmarks

            news_card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"{title}", weight=ft.FontWeight.BOLD, size=16, expand=True),
                        ft.IconButton(
                            icon = ft.Icons.BOOKMARK if is_bookmarked else ft.Icons.BOOKMARK_BORDER,
                            icon_color = "blue" if is_bookmarked else None,
                            tooltip = "Bookmark Article",
                            on_click = lambda e, 
                                        guid = article_guid,
                                        title = title,
                                        full_text = full_text,
                                        pub_date = pub_date,
                                        source = source: toggle_bookmark(
                                            e, guid, title, full_text, pub_date, source, page
                                        ),
                        )
                    ]),
                    ft.Text(full_text, size=14, italic=True),
                    ft.Text(f"{pub_date} | {source}", size=12, color="gray"),
                    ft.Text(f"{(', '.join(list_of_tags))}", size = 10)
                ], spacing=5),
                padding=10,
                border_radius=10,
                border=ft.border.all(1, "gray"),
                margin=5,
                on_click=article_closure(full_text, title, article_guid, pub_date, source),
                ink=True  
            )
            news_list.controls.append(news_card)

        news_list.update()

    except Exception as e:
        news_list.controls.append(ft.Text(f"Error fetching feed: {str(e)}", color="red"))
        news_list.update()

def main(page: ft.Page):
    page.title = "RSS Feed Parser"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO

    feed_url_input = ft.TextField(hint_text="Enter RSS Feed URL", expand=True)
    fetch_button = ft.ElevatedButton("Fetch News")
    bookmarks_button = ft.ElevatedButton("Show Bookmarks", icon=ft.Icons.BOOKMARK)
    news_list = ft.Column(scroll=ft.ScrollMode.AUTO)

    def on_fetch_click(e):
        page.current_view = ("feed")
        news_list.controls.clear()
        fetch_feed(feed_url_input.value, news_list, page)

    fetch_button.on_click = on_fetch_click

    def on_bookmarks_click(e):
        show_bookmarks(page, news_list)

    bookmarks_button.on_click = on_bookmarks_click    

    global modal_title, modal_content, article_dialog, current_article_url, current_article_title, current_article_date, current_article_source, bookmark_button
    current_article_url = None
    current_article_title = ""
    current_article_text = ""
    current_article_date = ""
    current_article_source = ""
    modal_title = ft.Text("", weight=ft.FontWeight.BOLD, size=18)
    modal_content = ft.Markdown("", selectable=True)

    def toggle_current_bookmark(e):
        if current_article_url:
            toggle_bookmark(
                e,
                current_article_url,
                current_article_title,
                current_article_text,
                current_article_date,
                current_article_source,
                page,
                news_list
            )
            bookmark_button.icon = ft.Icons.BOOKMARK if current_article_url in load_bookmarks(page) else ft.Icons.BOOKMARK_BORDER
            bookmark_button.update()

    bookmark_button = ft.IconButton(
        icon = ft.Icons.BOOKMARK_BORDER,
        tooltip = "Bookmark Article",
        on_click = toggle_current_bookmark,
    )


    def closeDialogue(e):
        article_dialog.open = False
        page.update()
    
    article_dialog = ft.AlertDialog(
        title= ft.Row([modal_title, ft.Container(expand=True), bookmark_button]),
        content=ft.Container(content=modal_content, padding=10, height=400, width=600),
        actions=[
            ft.TextButton("Open in Browser", on_click=lambda e: page.launch_url(current_article_url)),
            ft.TextButton("Close", on_click=closeDialogue),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )


    page.add(
        ft.Column([
            ft.Row([feed_url_input, fetch_button, bookmarks_button]),
            ft.Divider(),
            news_list
        ], 
        spacing=10)
    )

ft.app(target=main, view = ft.WEB_BROWSER)
