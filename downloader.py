#!/usr/bin/env python3

import os
import datetime
import urllib.request
from PIL import Image
from collections import OrderedDict


def getPageLinks(year):
    if year == 2023:
        data = urllib.request.urlopen("https://www.nhc.noaa.gov/archive/xgtwo/gtwo_archive_list.php?basin=atl").read()  # For 2023 data
    else:
        data = urllib.request.urlopen("https://www.nhc.noaa.gov/archive/xgtwo_5day/gtwo_archive_list.php?basin=atl").read()  # For old data

    text = data.decode()
    lines = text.split("\n")

    info_line = None
    for line in lines:
        if "archive/xgtwo_5day/gtwo_archive" in line:  # For data prior to 2023
            info_line = line
            break
        if "/archive/xgtwo/gtwo_archive.php?basin=atl" in line:  # For the 2023 data
            info_line = line
            break

    if info_line is None:
        raise Exception("Could not find line with all the data")

    output = OrderedDict()

    links = str(info_line).split("<br>")
    for link in links:
        if "latest available" not in link:
            link = link.strip()
            start_text = "href="
            link_start_index = link.find(start_text) + len(start_text) + 1
            link_text = link[link_start_index:]
            link_end_index = link_text.find('"')
            date_end_index = link_text.find("<")
            date_str = link_text[link_end_index + 2:date_end_index]
            link_text = link_text[0:link_end_index]

            if link_text != "":
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                output[date_obj] = f"https://www.nhc.noaa.gov/{link_text}"

    return output


def filterByYear(data, year):
    output = {}
    for data_point in data:
        if data_point.year == year:
            output[data_point] = data[data_point]

    return output


def getImageId(page_link: str):
    find_str = "current_issuance="
    id_start = page_link.find(find_str) + len(find_str)

    image_id = int(page_link[id_start:])
    return image_id


def getImageLink(image_id: int, year, image_with_clouds):
    if year == 2023:
        if image_with_clouds:
            image_link = f"https://www.nhc.noaa.gov/archive/xgtwo/atl/{image_id}/two_atl_2d0.png"  # With clouds, 2023
        else:
            image_link = f"https://www.nhc.noaa.gov/archive/xgtwo/atl/{image_id}/two_atl_7d0.png"  # 7-day 2023
    else:
        if image_with_clouds:
            image_link = f"https://www.nhc.noaa.gov/archive/xgtwo_5day/atl/{image_id}/two_atl_2d0.png"  # With clouds, prior to 2023
        else:
            image_link = f"https://www.nhc.noaa.gov/archive/xgtwo_5day/atl/{image_id}/two_atl_5d0.png"  # 5-day prior to 2023

    return image_link


def downloadAllImages(year, images_with_clouds):
    page_links = getPageLinks(year)
    page_links = filterByYear(page_links, year)
    dates = list(page_links.keys())
    page_links = list(page_links.values())

    dates.reverse()
    page_links.reverse()

    image_ids = [getImageId(page) for page in page_links]
    image_links = [getImageLink(image_id, year, images_with_clouds) for image_id in image_ids]

    cloud_str = "clouds" if images_with_clouds else "no_clouds"
    folder_name = f"{year}/{cloud_str}"

    if not os.path.isdir(folder_name):
        os.makedirs(folder_name, exist_ok=True)

    images_downloaded = []

    for i in range(len(image_links)):
        date = dates[i]
        image_link = image_links[i]
        date_str = date.strftime("%Y-%m-%d_%H-%M")

        file_name = f"{folder_name}/{date_str}.png"

        if os.path.isfile(file_name):
            print(f"Skipping image for {date_str}")
            images_downloaded.append(file_name)
        else:
            print(f"Downloading image for {date_str} {i + 1} of {len(image_links)}")

            try:
                urllib.request.urlretrieve(image_link, file_name)
                images_downloaded.append(file_name)
            except Exception as e:
                print(f"Unable to download image for {date_str}: {e}")

    return images_downloaded


def makeGif(file_names, output_file_name):
    print("Making GIF")
    frame_rate = 10
    duration = int(len(file_names) / frame_rate)
    print(f"GIF will be {duration} seconds long")

    frames = [Image.open(image) for image in file_names]
    frame_one = frames[0]
    frame_one.save(f"{output_file_name}.gif", format="GIF", append_images=frames, save_all=True, duration=duration, loop=0)


if __name__ == '__main__':
    # target_year = 2023
    # clouds = False

    for target_year in [2020, 2021, 2022, 2023]:
        for clouds in [True, False]:
            cloud_string = "clouds" if clouds else "no_clouds"
            output_file = f"{target_year}_{cloud_string}"

            images = downloadAllImages(target_year, clouds)
            makeGif(images, output_file)

    # september = [i for i in images if "-09-" in i]
    # september = september[0:110]
    # makeGif(september, "2020_september")
