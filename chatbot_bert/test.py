# import regex
# import re 
# import string

# def clean_data_custom(words):
#         # remove numbers
#         words = re.sub(r'\d+', '', words)
#         # remove punctuation
#         words = words.translate(str.maketrans('', '', string.punctuation))
#         # drop emoji
#         emoj = re.compile("["
#                 u"\U0001F600-\U0001F64F"  # emoticons
#                 u"\U0001F300-\U0001F5FF"  # symbols & pictographs
#                 u"\U0001F680-\U0001F6FF"  # transport & map symbols
#                 u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
#                 u"\U00002500-\U00002BEF"  # chinese char
#                 u"\U00002702-\U000027B0"
#                 u"\U00002702-\U000027B0"
#                 u"\U000024C2-\U0001F251"
#                 u"\U0001f926-\U0001f937"
#                 u"\U00010000-\U0010ffff"
#                 u"\u2640-\u2642" 
#                 u"\u2600-\u2B55"
#                 u"\u200d"
#                 u"\u23cf"
#                 u"\u23e9"
#                 u"\u231a"
#                 u"\ufe0f"  # dingbats
#                 u"\u3030"
#                             "]+", re.UNICODE)
#         words = re.sub(emoj, '', words)
        
#         # remove non ascii
#         words = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', words)
#         # convert whitespaces to single space
#         words = re.sub(r'\s+', ' ', words)

#         return words

text = "Em ăn cơm chưa?"
# # words = regex.sub(
# #             # there is a space or an end of a string after it
# #             r"[^\w#@&]+(?=\s|$)|"
# #             # there is a space or beginning of a string before it
# #             # not followed by a number
# #             r"(\s|^)[^\w#@&]+(?=[^0-9\s])|"
# #             # not in between numbers and not . or @ or & or - or #
# #             # e.g. 10'000.00 or blabla@gmail.com
# #             # and not url characters
# #             r"(?<=[^0-9\s])[^\w._~:/?#\[\]()@!$&*+,;=-]+(?=[^0-9\s])",
# #             " ",
# #             text,
# #         ).split()

# print(clean_data_custom(text))



# under the sea
# from underthesea import sent_tokenize, pos_tag, ner
# from underthesea import word_tokenize

# # Phân đoạn văn bản thành các câu
# text = "Đây là ví dụ về cách sử dụng underthesea để tách từ trong tiếng Việt."
# tokens = word_tokenize(text)
# print(tokens) # ['Đây', 'là', 'ví dụ', 'về', 'cách', 'sử dụng', 'underthesea', 'để', 'tách', 'từ', 'trong', 'tiếng', 'Việt', '.']


from pyvi import ViTokenizer

text = "Đây là ví dụ về cách sử dụng VietnameseTokenizer để tách từ trong tiếng Việt."
tokens = ViTokenizer.tokenize(text)
print(tokens) # Đây là ví_dụ về cách sử_dụng VietnameseTokenizer để tách từ trong tiếng Việt .
