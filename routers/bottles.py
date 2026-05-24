"""漂流瓶路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from typing import List, Optional
from database import get_db
from models import DriftBottle, BottleComment, User
from schemas import BottleCreate, BottleOut, CommentCreate, CommentOut
from auth import get_current_user, get_optional_user
import random

router = APIRouter(prefix="/api/bottles", tags=["漂流瓶"])

# 简单关键词过滤
BAD_WORDS = ["广告", "加微信", "赚钱", "色情", "暴力"]


def simple_review(text: str) -> bool:
    """简单内容审核，返回True表示通过"""
    for word in BAD_WORDS:
        if word in text:
            return False
    return True


@router.post("", response_model=BottleOut)
async def throw_bottle(
    data: BottleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not simple_review(data.content):
        raise HTTPException(status_code=400, detail="内容包含不当词语，请修改后重新提交")

    bottle = DriftBottle(
        user_id=current_user.id,
        content=data.content,
        mood=data.mood,
        is_public=data.is_public,
        tags=data.tags or "",
        is_reviewed=True,  # 通过简单过滤即为已审核
    )
    db.add(bottle)
    await db.commit()
    await db.refresh(bottle)

    # 重新查询，预加载 comments 避免 MissingGreenlet
    result = await db.execute(
        select(DriftBottle)
        .where(DriftBottle.id == bottle.id)
        .options(selectinload(DriftBottle.comments))
    )
    bottle = result.scalar_one()

    out = BottleOut.model_validate(bottle)
    out.is_mine = True
    return out


@router.get("/random", response_model=BottleOut)
async def get_random_bottle(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """随机捞取一个漂流瓶"""
    query = select(DriftBottle).where(
        DriftBottle.is_public == True,
        DriftBottle.is_reviewed == True,
        DriftBottle.is_hidden == False,
    ).options(selectinload(DriftBottle.comments))

    # 排除自己的瓶子
    if current_user:
        query = query.where(DriftBottle.user_id != current_user.id)

    result = await db.execute(query)
    bottles = result.scalars().all()

    if not bottles:
        raise HTTPException(status_code=404, detail="海洋里暂时没有漂流瓶，来投一个吧～")

    bottle = random.choice(bottles)

    # 增加浏览次数
    await db.execute(
        update(DriftBottle).where(DriftBottle.id == bottle.id)
        .values(view_count=DriftBottle.view_count + 1)
    )
    await db.commit()

    out = BottleOut.model_validate(bottle)
    out.is_mine = current_user is not None and bottle.user_id == current_user.id
    return out


@router.get("/mine", response_model=List[BottleOut])
async def my_bottles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(DriftBottle)
        .where(DriftBottle.user_id == current_user.id)
        .options(selectinload(DriftBottle.comments))
        .order_by(DriftBottle.created_at.desc())
    )
    bottles = result.scalars().all()
    out_list = []
    for b in bottles:
        out = BottleOut.model_validate(b)
        out.is_mine = True
        out_list.append(out)
    return out_list


@router.post("/{bottle_id}/comments", response_model=CommentOut)
async def add_comment(
    bottle_id: int,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    result = await db.execute(
        select(DriftBottle).where(
            DriftBottle.id == bottle_id,
            DriftBottle.is_public == True,
            DriftBottle.is_hidden == False,
        )
    )
    bottle = result.scalar_one_or_none()
    if not bottle:
        raise HTTPException(status_code=404, detail="漂流瓶不存在或已被隐藏")

    if not simple_review(data.content):
        raise HTTPException(status_code=400, detail="评论包含不当词语")

    comment = BottleComment(
        bottle_id=bottle_id,
        user_id=current_user.id if current_user else None,
        nickname=data.nickname or "匿名旅人",
        content=data.content,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


@router.get("/{bottle_id}/comments", response_model=List[CommentOut])
async def get_comments(bottle_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BottleComment).where(
            BottleComment.bottle_id == bottle_id,
            BottleComment.is_hidden == False,
        ).order_by(BottleComment.created_at.asc())
    )
    return result.scalars().all()
