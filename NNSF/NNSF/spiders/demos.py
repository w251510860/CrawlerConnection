# -*- coding: utf-8 -*-
import scrapy

count = 0


class DemosSpider(scrapy.Spider):
    name = 'nsfc'
    allowed_domains = ['or.nsfc.gov.cn']

    def start_requests(self):  # 对scrapy原生方法进行改写
        requests_list = [
            ['http://or.nsfc.gov.cn/handle/00001903-5/2', '数理科学'],
            ['http://or.nsfc.gov.cn/handle/00001903-5/3', '化学科学'],
            ['http://or.nsfc.gov.cn/handle/00001903-5/4', '生命科学'],
            ['http://or.nsfc.gov.cn/handle/00001903-5/5', '地球科学'],
            ['http://or.nsfc.gov.cn/handle/00001903-5/6', '工程与材料科学'],
            ['http://or.nsfc.gov.cn/handle/00001903-5/7', '信息科学'],
            ['http://or.nsfc.gov.cn/handle/00001903-5/8', '管理科学'],
            ['http://or.nsfc.gov.cn/handle/00001903-5/9', '医学科学']
        ]
        return [scrapy.Request(item[0], meta={'topic': item[1], 'base_url': item[0], 'count': 0, 'page_count': 0},
                               callback=self.parse) for item in
                requests_list]

    def parse(self, response):
        count = response.meta['count']
        page_count = response.meta['page_count']
        paper_list_path = '//tr[position()>1]'
        paper_list = response.xpath(paper_list_path)
        if len(paper_list) == 0:  # 如果获取不到内容，说明已经爬完
            return None
        for paper in paper_list:
            item = dict()
            page_count += 1
            title_path = './td[@headers="t2"]/strong/a/text()'
            author_path = './td[@headers="t3"]/em/a/text()'
            detail_url_path = './td[@headers="t2"]/strong/a/@href'
            item['title'] = ''.join(paper.xpath(title_path).extract())  # 如果没有title本条数据无效直接解析下一条
            if not item['title']:
                count += 1
                print(f'null page count -> {count}')
                continue
            item['author'] = ','.join(paper.xpath(author_path).extract())  # 作者为多人，获取到的是一个list，用.join分别取出拼接成字符串
            detail_url = paper.xpath(detail_url_path)[0].extract()  # 获取详情页连接
            # yield scrapy.Request(f'http://or.nsfc.gov.cn{detail_url}', meta={'item': item}, callback=self.detail_page)
        base_url = response.meta['base_url']
        offset = response.meta.get('offset', 0)
        topic = response.meta.get('topic')
        offset = int(offset) + 20
        next_url = f'{base_url}?offset={offset}'  # 拼接下一页url
        print(f'page_count -> {page_count}')
        yield scrapy.Request(next_url,
                             meta={'topic': topic, 'offset': offset, 'base_url': base_url, 'count': count,
                                   'page_count': page_count},
                             callback=self.parse)

    def detail_page(self, response):
        base_path = '//div[div[contains(text(), "{}")]]/div[@class="col-2"]/text()'  # 因为其他xpath解析路径相似，所以做一个抽取，contains是xpath高级应用可以百度
        name_path = base_path.format('期刊名称')
        date_of_publication_path = base_path.format('发表日期')
        type_of_founding_path = base_path.format('资助类型')
        project_id_path = base_path.format('项目编号')
        chinese_project_name_path = base_path.format('项目名称')
        research_institute_path = base_path.format('研究机构')
        reference_method_path = '//div[div[contains(text(), "推荐引用方式")]]/div[@class="col-2"]/a/@href'
        result_subject_path = '//div[div[contains(text(), "成果所属学科")]]/div[@class="col-2"]//a/text()'
        license_path = base_path.format('使用许可')
        pdf_path = '//div[div[contains(text(), "全文下载")]]/div[@class="col-2"]//a/@href'

        item = response.meta['item']
        item['name'] = ''.join(response.xpath(name_path).extract()).strip().replace('\r', '').replace('\t', '').replace(
            '\n', '')
        item['date_of_publication'] = ''.join(response.xpath(date_of_publication_path).extract()).strip().replace('\r',
                                                                                                                  '').replace(
            '\t', '').replace('\n', '')
        item['type_of_founding'] = ''.join(response.xpath(type_of_founding_path).extract()).strip().replace('\r',
                                                                                                            '').replace(
            '\t', '').replace('\n', '')
        item['project_id'] = ''.join(response.xpath(project_id_path).extract()).strip().replace('\r', '').replace('\t',
                                                                                                                  '').replace(
            '\n', '')
        item['chinese_project_name'] = ''.join(response.xpath(chinese_project_name_path).extract()).strip().replace(
            '\r', '').replace('\t', '').replace('\n', '')
        item['research_institute'] = ''.join(response.xpath(research_institute_path).extract()).strip().replace('\r',
                                                                                                                '').replace(
            '\t', '').replace('\n', '')
        item['reference_method'] = ''.join(response.xpath(reference_method_path).extract()).strip().replace('\r',
                                                                                                            '').replace(
            '\t', '').replace('\n', '')
        item['result_subject'] = ''.join(response.xpath(result_subject_path).extract()).strip().replace('\r',
                                                                                                        '').replace(
            '\t', '').replace('\n', '')
        item['license'] = ''.join(response.xpath(license_path).extract()).strip().replace('\r', '').replace('\t',
                                                                                                            '').replace(
            '\n', '')
        pdf = ''.join(response.xpath(pdf_path).extract()).strip().replace('\r', '').replace('\t', '').replace('\n', '')
        if pdf:
            item['pdf'] = 'http://or.nsfc.gov.cn/{}'.format(pdf)
        else:
            item['pdf'] = ''
        # yield item
