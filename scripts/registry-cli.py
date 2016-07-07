#!/usr/bin/env python

"""A command-line client for the Docker registry."""

import argparse

import requests


def list_cmd(args):
    """List images"""
    url = args.registry + '/v2/_catalog'
    r = requests.get(url)
    data = r.json()
    for repo in data['repositories']:
        print(repo)


def list_tags_cmd(args):
    """List tags for an image"""
    url = args.registry + '/v2/' + args.name + '/tags/list'
    r = requests.get(url)
    data = r.json()
    if data['tags'] is None:
        print('No tags for {}'.format(args.name))
        return
    for repo in data['tags']:
        print(repo)


def delete_tag_cmd(args):
    """Delete a tag from an image"""
    url = args.registry + '/v2/' + args.name + '/manifests/' + args.tag
    header = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
    r = requests.get(url, headers=header)
    if r.status_code == 404:
        print('image/tag combination not found')
        return
    digest = r.headers['Docker-Content-Digest']
    url = args.registry + '/v2/' + args.name + '/manifests/' + digest
    r = requests.delete(url, headers=header)
    if r.status_code != 202:
        print('error')
    else:
        print('deleted')


def main():
    """Main entrypoint."""
    parser = argparse.ArgumentParser(description="Docker Registry client")
    parser.add_argument("-r", "--registry", help="Registry URL", default="http:127.0.0.1:5000")

    subparser = parser.add_subparsers()

    argparser_list = subparser.add_parser('list', help="Lists all the images in the registry")
    argparser_list.set_defaults(func=list_cmd)

    argparser_list_tags = subparser.add_parser('list-tags', help="Lists all tags for an image")
    argparser_list_tags.add_argument('name', help="Name of the image")
    argparser_list_tags.set_defaults(func=list_tags_cmd)

    argparser_list_tags = subparser.add_parser('delete', help="Delete a tag from an image")
    argparser_list_tags.add_argument('name', help="Name of the image")
    argparser_list_tags.add_argument('tag', help="Name of the tag to delete")
    argparser_list_tags.set_defaults(func=delete_tag_cmd)

    args = parser.parse_args()

    args.func(args)

if __name__ == "__main__":
    main()
