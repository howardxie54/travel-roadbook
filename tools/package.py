"""Build portable ZIPs using only Python's standard library."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent


def eligible(path):
    rel = path.relative_to(ROOT)
    return not any(part in {'.git', 'dist', '__pycache__', '.venv', 'node_modules'} for part in rel.parts) and not path.name.startswith('.env') and path.suffix not in {'.pyc', '.pyo'}


def skill_file(path):
    rel = path.relative_to(ROOT)
    return rel.parts[0] in {'scripts', 'references', 'assets'} or (rel.parts[0] == 'examples' and len(rel.parts) == 2) or str(rel) in {'SKILL.md', 'LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md'}


def write_zip(output, paths, compact=False):
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            name = 'travel-roadbook/' + path.relative_to(ROOT).as_posix()
            archive.writestr(name, path.read_bytes())
        if compact:
            readme = '''# Travel Roadbook · 旅行路书 Skill

将 travel-roadbook 目录放入宿主技能目录。Codex 通常为
~/.codex/skills/travel-roadbook；Windows 为
%USERPROFILE%\\.codex\\skills\\travel-roadbook。
开启新对话后输入 $travel-roadbook 并描述旅行计划。

生成器使用 Python 3.7+ 标准库，无需安装其他设计 Skill。
联网和图片生成取决于宿主工具；入口及完整规则见 SKILL.md。

本轻量包包含全部基础运行文件和修改/订单测试数据。
日本精修演示、真实截图及完整说明在 GitHub 源码包中：
https://github.com/howardxie54/travel-roadbook

限非商业使用：见 LICENSE、NOTICE 与 THIRD_PARTY_NOTICES.md。
'''
            archive.writestr('travel-roadbook/README.md', readme.encode('utf-8'))


def main():
    out = ROOT / 'dist'
    out.mkdir(exist_ok=True)
    files = [p for p in ROOT.rglob('*') if p.is_file() and eligible(p)]
    bundles = [('travel-roadbook-技能包.zip', [p for p in files if skill_file(p)]), ('travel-roadbook-GitHub源码.zip', files)]
    hashes = []
    for name, paths in bundles:
        output = out / name
        compact = name == 'travel-roadbook-技能包.zip'
        write_zip(output, paths, compact)
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        hashes.append(digest + '  ' + name)
        print(json.dumps({'archive': name, 'files': len(paths) + int(compact), 'bytes': output.stat().st_size, 'sha256': digest}, ensure_ascii=False))
    (out / 'SHA256SUMS.txt').write_text('\n'.join(hashes) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
